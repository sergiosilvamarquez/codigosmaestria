"""
Modelo energético principal con optimización multiobjetivo
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import cvxpy as cp
from scipy import optimize
import warnings

@dataclass
class RecursoEnergetico:
    """Clase para representar un recurso energético"""
    nombre: str
    capacidad_maxima: float  # kWh/año
    factor_energia: float    # kWh/unidad
    costo_unitario: float   # $/kWh
    factor_emision: float   # kgCO2/kWh
    factor_social: float    # índice social
    vida_util: float        # años
    costo_mantenimiento: float  # %/año
    eficiencia: Dict[str, float]  # eficiencia por tarea
    rampa_maxima: Optional[float] = None  # kW/h límite de rampa
    almacenable: bool = False
    
@dataclass
class Tarea:
    """Clase para representar una tarea/demanda energética"""
    nombre: str
    demanda_anual: float     # kWh/año
    potencia_maxima: float   # kW
    perfil_temporal: Optional[np.ndarray] = None  # perfil horario normalizado
    prioridad: int = 1       # 1=alta, 2=media, 3=baja
    factor_carga: float = 0.8

@dataclass
class ResultadoOptimizacion:
    """Clase para almacenar resultados de optimización"""
    asignaciones: Dict[str, Dict[str, float]]
    costo_total: float
    emisiones_co2: float
    factor_social: float
    estado_optimizacion: str
    tiempo_solucion: float
    pareto_front: Optional[np.ndarray] = None
    
class ModeloEnergetico:
    """
    Modelo principal para optimización energética sustentable
    
    Características:
    - Optimización multiobjetivo (costo, CO2, social)
    - Modelado temporal con almacenamiento
    - Análisis de incertidumbre
    - Múltiples algoritmos de solución
    """
    
    def __init__(self, horizonte_temporal: int = 8760):
        """
        Inicializa el modelo energético
        
        Args:
            horizonte_temporal: Número de períodos (horas) a optimizar
        """
        self.recursos: Dict[str, RecursoEnergetico] = {}
        self.tareas: Dict[str, Tarea] = {}
        self.horizonte_temporal = horizonte_temporal
        self.almacenamiento_config = None
        self._variables_optimizacion = None
        self._restricciones = []
        
    def agregar_recurso(self, recurso: RecursoEnergetico) -> None:
        """Agrega un recurso energético al modelo"""
        self.recursos[recurso.nombre] = recurso
        
    def agregar_tarea(self, tarea: Tarea) -> None:
        """Agrega una tarea/demanda al modelo"""
        self.tareas[tarea.nombre] = tarea
        
    def configurar_almacenamiento(self, capacidad: float, eficiencia: float, 
                                 autodescarga: float = 0.001) -> None:
        """
        Configura sistema de almacenamiento de energía
        
        Args:
            capacidad: Capacidad máxima de almacenamiento (kWh)
            eficiencia: Eficiencia de carga/descarga (0-1)
            autodescarga: Tasa de autodescarga por hora (0-1)
        """
        self.almacenamiento_config = {
            'capacidad': capacidad,
            'eficiencia': eficiencia,
            'autodescarga': autodescarga
        }
        
    def _crear_variables_optimizacion(self) -> Dict[str, cp.Variable]:
        """Crea variables de optimización CVXPY"""
        recursos_nombres = list(self.recursos.keys())
        tareas_nombres = list(self.tareas.keys())
        
        variables = {}
        
        # Variables principales: asignación recurso-tarea por período
        variables['x'] = cp.Variable(
            (len(recursos_nombres), len(tareas_nombres), self.horizonte_temporal),
            nonneg=True, name='asignacion'
        )
        
        # Variables de almacenamiento si está configurado
        if self.almacenamiento_config:
            variables['storage'] = cp.Variable(
                self.horizonte_temporal, nonneg=True, name='almacenamiento'
            )
            variables['charge'] = cp.Variable(
                self.horizonte_temporal, nonneg=True, name='carga'
            )
            variables['discharge'] = cp.Variable(
                self.horizonte_temporal, nonneg=True, name='descarga'
            )
            
        return variables
        
    def _crear_funciones_objetivo(self, variables: Dict[str, cp.Variable]) -> Dict[str, cp.Expression]:
        """Crea las tres funciones objetivo"""
        recursos_nombres = list(self.recursos.keys())
        tareas_nombres = list(self.tareas.keys())
        x = variables['x']
        
        # Función objetivo 1: Minimizar costos
        costo_operacion = 0
        costo_construccion = 0
        
        for i, recurso_nombre in enumerate(recursos_nombres):
            recurso = self.recursos[recurso_nombre]
            for j, tarea_nombre in enumerate(tareas_nombres):
                # Costos operativos
                costo_operacion += cp.sum(
                    x[i, j, :] * recurso.factor_energia * recurso.costo_unitario
                )
                # Costos de construcción anualizados
                capacidad_instalada = cp.max(x[i, j, :])
                costo_construccion += capacidad_instalada * self._costo_capital_anualizado(recurso)
                
        objetivo_costo = costo_operacion + costo_construccion
        
        # Función objetivo 2: Minimizar emisiones CO2
        emisiones_operacion = 0
        emisiones_construccion = 0
        
        for i, recurso_nombre in enumerate(recursos_nombres):
            recurso = self.recursos[recurso_nombre]
            for j, tarea_nombre in enumerate(tareas_nombres):
                # Emisiones operativas
                emisiones_operacion += cp.sum(
                    x[i, j, :] * recurso.factor_emision
                )
                # Emisiones de construcción (simplificado)
                capacidad_instalada = cp.max(x[i, j, :])
                emisiones_construccion += capacidad_instalada * 0.1  # factor típico
                
        objetivo_co2 = emisiones_operacion + emisiones_construccion
        
        # Función objetivo 3: Maximizar factor social
        factor_social = 0
        
        for i, recurso_nombre in enumerate(recursos_nombres):
            recurso = self.recursos[recurso_nombre]
            for j, tarea_nombre in enumerate(tareas_nombres):
                tarea = self.tareas[tarea_nombre]
                # Factor social ponderado por utilización
                utilizacion = cp.sum(x[i, j, :]) / (tarea.demanda_anual + 1e-6)
                factor_social += utilizacion * recurso.factor_social
                
        objetivo_social = -factor_social  # Negativo para maximizar
        
        return {
            'costo': objetivo_costo,
            'co2': objetivo_co2,
            'social': objetivo_social
        }
        
    def _crear_restricciones(self, variables: Dict[str, cp.Variable]) -> List[cp.Constraint]:
        """Crea restricciones del modelo"""
        recursos_nombres = list(self.recursos.keys())
        tareas_nombres = list(self.tareas.keys())
        x = variables['x']
        restricciones = []
        
        # Restricción 1: Balance de energía por tarea y período
        for j, tarea_nombre in enumerate(tareas_nombres):
            tarea = self.tareas[tarea_nombre]
            for t in range(self.horizonte_temporal):
                demanda_t = self._obtener_demanda_temporal(tarea, t)
                
                energia_suministrada = 0
                for i, recurso_nombre in enumerate(recursos_nombres):
                    recurso = self.recursos[recurso_nombre]
                    eficiencia = recurso.eficiencia.get(tarea_nombre, 0.8)
                    energia_suministrada += (
                        x[i, j, t] * recurso.factor_energia * eficiencia
                    )
                
                # Incluir descarga de almacenamiento si existe
                if self.almacenamiento_config and 'discharge' in variables:
                    energia_suministrada += variables['discharge'][t]
                    
                restricciones.append(energia_suministrada >= demanda_t)
                
        # Restricción 2: Límites de capacidad de recursos
        for i, recurso_nombre in enumerate(recursos_nombres):
            recurso = self.recursos[recurso_nombre]
            for t in range(self.horizonte_temporal):
                uso_total = cp.sum(x[i, :, t])
                restricciones.append(uso_total <= recurso.capacidad_maxima / self.horizonte_temporal)
                
        # Restricción 3: Límites de potencia
        for i, recurso_nombre in enumerate(recursos_nombres):
            recurso = self.recursos[recurso_nombre]
            if recurso.rampa_maxima:
                for t in range(1, self.horizonte_temporal):
                    cambio_potencia = cp.sum(x[i, :, t]) - cp.sum(x[i, :, t-1])
                    restricciones.append(cambio_potencia <= recurso.rampa_maxima)
                    restricciones.append(cambio_potencia >= -recurso.rampa_maxima)
                    
        # Restricciones de almacenamiento
        if self.almacenamiento_config and 'storage' in variables:
            storage = variables['storage']
            charge = variables['charge']
            discharge = variables['discharge']
            config = self.almacenamiento_config
            
            # Capacidad máxima
            restricciones.append(storage <= config['capacidad'])
            
            # Balance de almacenamiento
            for t in range(1, self.horizonte_temporal):
                balance = (storage[t-1] * (1 - config['autodescarga']) +
                          charge[t] * config['eficiencia'] - discharge[t])
                restricciones.append(storage[t] == balance)
                
            # Estado inicial
            restricciones.append(storage[0] == 0)
            
        return restricciones
        
    def _obtener_demanda_temporal(self, tarea: Tarea, t: int) -> float:
        """Obtiene la demanda en el período t para una tarea"""
        if tarea.perfil_temporal is not None:
            periodo_normalizado = t % len(tarea.perfil_temporal)
            factor_temporal = tarea.perfil_temporal[periodo_normalizado]
        else:
            # Perfil plano si no se especifica
            factor_temporal = 1.0 / self.horizonte_temporal
            
        return tarea.demanda_anual * factor_temporal
        
    def _costo_capital_anualizado(self, recurso: RecursoEnergetico, tasa_descuento: float = 0.08) -> float:
        """Calcula el costo de capital anualizado"""
        n = recurso.vida_util
        factor_anualizado = (tasa_descuento * (1 + tasa_descuento)**n) / \
                           ((1 + tasa_descuento)**n - 1)
        # Estimación simplificada del costo de capital
        costo_capital = recurso.costo_unitario * 10  # Factor típico
        return costo_capital * factor_anualizado
        
    def optimizar_objetivo_unico(self, objetivo: str = 'costo') -> ResultadoOptimizacion:
        """
        Optimiza un solo objetivo
        
        Args:
            objetivo: 'costo', 'co2', o 'social'
            
        Returns:
            ResultadoOptimizacion con la solución óptima
        """
        import time
        inicio = time.time()
        
        # Crear variables y funciones objetivo
        variables = self._crear_variables_optimizacion()
        objetivos = self._crear_funciones_objetivo(variables)
        restricciones = self._crear_restricciones(variables)
        
        # Resolver problema
        problema = cp.Problem(cp.Minimize(objetivos[objetivo]), restricciones)
        
        try:
            problema.solve(solver=cp.ECOS, verbose=False)
            
            if problema.status == cp.OPTIMAL:
                tiempo_solucion = time.time() - inicio
                
                # Extraer resultados
                asignaciones = self._extraer_asignaciones(variables)
                
                return ResultadoOptimizacion(
                    asignaciones=asignaciones,
                    costo_total=objetivos['costo'].value,
                    emisiones_co2=objetivos['co2'].value,
                    factor_social=-objetivos['social'].value,
                    estado_optimizacion=problema.status,
                    tiempo_solucion=tiempo_solucion
                )
            else:
                raise ValueError(f"Optimización falló: {problema.status}")
                
        except Exception as e:
            return ResultadoOptimizacion(
                asignaciones={},
                costo_total=float('inf'),
                emisiones_co2=float('inf'),
                factor_social=0,
                estado_optimizacion=f"Error: {str(e)}",
                tiempo_solucion=time.time() - inicio
            )
            
    def _extraer_asignaciones(self, variables: Dict[str, cp.Variable]) -> Dict[str, Dict[str, float]]:
        """Extrae las asignaciones de las variables optimizadas"""
        recursos_nombres = list(self.recursos.keys())
        tareas_nombres = list(self.tareas.keys())
        x = variables['x']
        
        asignaciones = {}
        
        for i, recurso_nombre in enumerate(recursos_nombres):
            asignaciones[recurso_nombre] = {}
            for j, tarea_nombre in enumerate(tareas_nombres):
                # Suma sobre todos los períodos temporales
                asignacion_total = np.sum(x.value[i, j, :]) if x.value is not None else 0
                asignaciones[recurso_nombre][tarea_nombre] = float(asignacion_total)
                
        return asignaciones
        
    def optimizar_multiobjetivo_ponderacion(self, pesos: Dict[str, float]) -> ResultadoOptimizacion:
        """
        Optimización multiobjetivo por ponderación
        
        Args:
            pesos: Diccionario con pesos para cada objetivo {'costo': w1, 'co2': w2, 'social': w3}
        """
        # Validar pesos
        suma_pesos = sum(pesos.values())
        if not np.isclose(suma_pesos, 1.0):
            pesos = {k: v/suma_pesos for k, v in pesos.items()}
            
        # Normalizar objetivos (resolver cada uno individualmente primero)
        resultado_costo = self.optimizar_objetivo_unico('costo')
        resultado_co2 = self.optimizar_objetivo_unico('co2')
        resultado_social = self.optimizar_objetivo_unico('social')
        
        # Rangos para normalización
        rango_costo = resultado_costo.costo_total
        rango_co2 = resultado_co2.emisiones_co2
        rango_social = resultado_social.factor_social
        
        # Crear problema ponderado
        variables = self._crear_variables_optimizacion()
        objetivos = self._crear_funciones_objetivo(variables)
        restricciones = self._crear_restricciones(variables)
        
        # Función objetivo ponderada y normalizada
        objetivo_ponderado = (
            pesos.get('costo', 0) * objetivos['costo'] / (rango_costo + 1e-6) +
            pesos.get('co2', 0) * objetivos['co2'] / (rango_co2 + 1e-6) +
            pesos.get('social', 0) * objetivos['social'] / (rango_social + 1e-6)
        )
        
        problema = cp.Problem(cp.Minimize(objetivo_ponderado), restricciones)
        
        import time
        inicio = time.time()
        
        try:
            problema.solve(solver=cp.ECOS, verbose=False)
            
            if problema.status == cp.OPTIMAL:
                asignaciones = self._extraer_asignaciones(variables)
                
                return ResultadoOptimizacion(
                    asignaciones=asignaciones,
                    costo_total=objetivos['costo'].value,
                    emisiones_co2=objetivos['co2'].value,
                    factor_social=-objetivos['social'].value,
                    estado_optimizacion=problema.status,
                    tiempo_solucion=time.time() - inicio
                )
            else:
                raise ValueError(f"Optimización falló: {problema.status}")
                
        except Exception as e:
            return ResultadoOptimizacion(
                asignaciones={},
                costo_total=float('inf'),
                emisiones_co2=float('inf'),
                factor_social=0,
                estado_optimizacion=f"Error: {str(e)}",
                tiempo_solucion=time.time() - inicio
            )
            
    def analisis_sensibilidad(self, parametro: str, variacion: float = 0.1, 
                            n_puntos: int = 11) -> pd.DataFrame:
        """
        Realiza análisis de sensibilidad variando un parámetro
        
        Args:
            parametro: Nombre del parámetro a variar
            variacion: Porcentaje de variación (±)
            n_puntos: Número de puntos a evaluar
            
        Returns:
            DataFrame con resultados del análisis
        """
        factores = np.linspace(1-variacion, 1+variacion, n_puntos)
        resultados = []
        
        for factor in factores:
            # Modificar temporalmente el parámetro
            self._modificar_parametro(parametro, factor)
            
            # Optimizar
            resultado = self.optimizar_objetivo_unico('costo')
            
            resultados.append({
                'factor': factor,
                'variacion_pct': (factor - 1) * 100,
                'costo': resultado.costo_total,
                'co2': resultado.emisiones_co2,
                'social': resultado.factor_social,
                'estado': resultado.estado_optimizacion
            })
            
            # Restaurar parámetro original
            self._modificar_parametro(parametro, 1/factor)
            
        return pd.DataFrame(resultados)
        
    def _modificar_parametro(self, parametro: str, factor: float) -> None:
        """Modifica temporalmente un parámetro del modelo"""
        # Implementación simplificada - modificar costos
        if parametro == 'costos':
            for recurso in self.recursos.values():
                recurso.costo_unitario *= factor
        elif parametro == 'emisiones':
            for recurso in self.recursos.values():
                recurso.factor_emision *= factor
        # Agregar más parámetros según necesidad
        
    def generar_frente_pareto(self, n_puntos: int = 50) -> np.ndarray:
        """
        Genera frente Pareto usando ε-restricción
        
        Args:
            n_puntos: Número de puntos del frente Pareto
            
        Returns:
            Array con puntos del frente Pareto [costo, co2, social]
        """
        # Obtener rangos de objetivos
        min_costo = self.optimizar_objetivo_unico('costo')
        min_co2 = self.optimizar_objetivo_unico('co2')
        max_social = self.optimizar_objetivo_unico('social')
        
        # Rangos para ε-restricción
        rango_co2 = np.linspace(min_co2.emisiones_co2, min_costo.emisiones_co2, n_puntos)
        
        puntos_pareto = []
        
        for epsilon_co2 in rango_co2:
            try:
                # Optimizar costo sujeto a restricción de CO2
                resultado = self._optimizar_con_restriccion_epsilon('costo', 'co2', epsilon_co2)
                
                if resultado.estado_optimizacion == cp.OPTIMAL:
                    puntos_pareto.append([
                        resultado.costo_total,
                        resultado.emisiones_co2,
                        resultado.factor_social
                    ])
            except:
                continue
                
        return np.array(puntos_pareto)
        
    def _optimizar_con_restriccion_epsilon(self, objetivo_principal: str, 
                                         objetivo_restriccion: str, 
                                         epsilon: float) -> ResultadoOptimizacion:
        """Optimización con restricción ε"""
        variables = self._crear_variables_optimizacion()
        objetivos = self._crear_funciones_objetivo(variables)
        restricciones = self._crear_restricciones(variables)
        
        # Agregar restricción ε
        restricciones.append(objetivos[objetivo_restriccion] <= epsilon)
        
        # Resolver
        problema = cp.Problem(cp.Minimize(objetivos[objetivo_principal]), restricciones)
        problema.solve(solver=cp.ECOS, verbose=False)
        
        asignaciones = self._extraer_asignaciones(variables) if problema.status == cp.OPTIMAL else {}
        
        return ResultadoOptimizacion(
            asignaciones=asignaciones,
            costo_total=objetivos['costo'].value if objetivos['costo'].value else float('inf'),
            emisiones_co2=objetivos['co2'].value if objetivos['co2'].value else float('inf'),
            factor_social=-objetivos['social'].value if objetivos['social'].value else 0,
            estado_optimizacion=problema.status,
            tiempo_solucion=0
        )
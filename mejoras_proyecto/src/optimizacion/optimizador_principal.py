"""
Optimizador principal que integra todos los métodos de optimización
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from ..modelos.modelo_energetico import ModeloEnergetico, ResultadoOptimizacion
from ..modelos.validacion import ValidadorParametros
from .algoritmos_multiobjetivo import NSGA2, AlgoritmoTOPSIS
from .analisis_incertidumbre import AnalizadorIncertidumbre

class OptimizadorEnergetico:
    """
    Optimizador principal que integra múltiples métodos de optimización
    
    Características:
    - Múltiples algoritmos de optimización
    - Análisis de incertidumbre
    - Paralelización automática
    - Validación integrada
    - Logging detallado
    """
    
    def __init__(self, modelo: ModeloEnergetico, validar_modelo: bool = True):
        """
        Inicializa el optimizador
        
        Args:
            modelo: Modelo energético a optimizar
            validar_modelo: Si realizar validación automática
        """
        self.modelo = modelo
        self.validador = ValidadorParametros(modelo)
        self.analizador_incertidumbre = AnalizadorIncertidumbre(modelo)
        
        # Configurar logging
        self.logger = logging.getLogger(__name__)
        
        # Resultados de optimización
        self.resultados_cache: Dict[str, ResultadoOptimizacion] = {}
        self.frente_pareto_cache: Optional[np.ndarray] = None
        
        # Validar modelo si se solicita
        if validar_modelo:
            self._validar_modelo_inicial()
            
    def _validar_modelo_inicial(self) -> None:
        """Valida el modelo al inicio"""
        es_valido, errores = self.validador.validar_completo()
        
        if not es_valido:
            errores_criticos = [e for e in errores if e.severidad == "error"]
            mensaje_error = f"Modelo con {len(errores_criticos)} errores críticos. "
            mensaje_error += "Usar validador.generar_reporte_validacion() para detalles."
            
            self.logger.error(mensaje_error)
            warnings.warn(mensaje_error, UserWarning)
            
            # Intentar corrección automática
            correcciones = self.validador.corregir_automaticamente()
            if correcciones:
                self.logger.info(f"Aplicadas {len(correcciones)} correcciones automáticas")
                for correccion in correcciones:
                    self.logger.info(f"  - {correccion}")
                    
    def optimizar_objetivo_unico(self, objetivo: str = 'costo', 
                                metodo: str = 'cvxpy') -> ResultadoOptimizacion:
        """
        Optimiza un solo objetivo usando diferentes métodos
        
        Args:
            objetivo: 'costo', 'co2', o 'social'
            metodo: 'cvxpy', 'scipy', 'pulp'
            
        Returns:
            ResultadoOptimizacion
        """
        clave_cache = f"{objetivo}_{metodo}"
        
        if clave_cache in self.resultados_cache:
            self.logger.info(f"Usando resultado en cache para {clave_cache}")
            return self.resultados_cache[clave_cache]
            
        self.logger.info(f"Optimizando objetivo único: {objetivo} con método {metodo}")
        
        try:
            if metodo == 'cvxpy':
                resultado = self.modelo.optimizar_objetivo_unico(objetivo)
            elif metodo == 'scipy':
                resultado = self._optimizar_con_scipy(objetivo)
            elif metodo == 'pulp':
                resultado = self._optimizar_con_pulp(objetivo)
            else:
                raise ValueError(f"Método {metodo} no reconocido")
                
            self.resultados_cache[clave_cache] = resultado
            self.logger.info(f"Optimización completada en {resultado.tiempo_solucion:.2f}s")
            
            return resultado
            
        except Exception as e:
            self.logger.error(f"Error en optimización: {str(e)}")
            return ResultadoOptimizacion(
                asignaciones={},
                costo_total=float('inf'),
                emisiones_co2=float('inf'),
                factor_social=0,
                estado_optimizacion=f"Error: {str(e)}",
                tiempo_solucion=0
            )
            
    def optimizar_multiobjetivo(self, metodo: str = 'nsga2', 
                               parametros: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Optimización multiobjetivo usando diferentes algoritmos
        
        Args:
            metodo: 'nsga2', 'ponderacion', 'epsilon_restriccion', 'topsis'
            parametros: Parámetros específicos del método
            
        Returns:
            Diccionario con resultados del método multiobjetivo
        """
        if parametros is None:
            parametros = {}
            
        self.logger.info(f"Iniciando optimización multiobjetivo: {metodo}")
        inicio = time.time()
        
        try:
            if metodo == 'nsga2':
                resultado = self._optimizar_nsga2(parametros)
            elif metodo == 'ponderacion':
                resultado = self._optimizar_ponderacion(parametros)
            elif metodo == 'epsilon_restriccion':
                resultado = self._optimizar_epsilon_restriccion(parametros)
            elif metodo == 'topsis':
                resultado = self._optimizar_topsis(parametros)
            else:
                raise ValueError(f"Método multiobjetivo {metodo} no reconocido")
                
            tiempo_total = time.time() - inicio
            resultado['tiempo_total'] = tiempo_total
            
            self.logger.info(f"Optimización multiobjetivo completada en {tiempo_total:.2f}s")
            return resultado
            
        except Exception as e:
            self.logger.error(f"Error en optimización multiobjetivo: {str(e)}")
            return {
                'error': str(e),
                'metodo': metodo,
                'tiempo_total': time.time() - inicio
            }
            
    def _optimizar_nsga2(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Optimización usando NSGA-II"""
        
        # Parámetros por defecto
        config = {
            'poblacion': parametros.get('poblacion', 100),
            'generaciones': parametros.get('generaciones', 200),
            'prob_cruce': parametros.get('prob_cruce', 0.9),
            'prob_mutacion': parametros.get('prob_mutacion', 0.1)
        }
        
        # Inicializar algoritmo NSGA-II
        nsga2 = NSGA2(self.modelo, **config)
        
        # Ejecutar optimización
        frente_pareto, poblacion_final, convergencia = nsga2.optimizar()
        
        # Procesar resultados
        mejores_soluciones = []
        for individuo in frente_pareto:
            # Convertir individuo a ResultadoOptimizacion
            resultado = self._convertir_individuo_a_resultado(individuo)
            mejores_soluciones.append(resultado)
            
        return {
            'metodo': 'nsga2',
            'frente_pareto': frente_pareto,
            'mejores_soluciones': mejores_soluciones,
            'convergencia': convergencia,
            'configuracion': config,
            'n_soluciones_pareto': len(frente_pareto)
        }
        
    def _optimizar_ponderacion(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Optimización por ponderación de objetivos"""
        
        # Pesos por defecto o especificados
        pesos_sets = parametros.get('pesos_sets', [
            {'costo': 0.6, 'co2': 0.3, 'social': 0.1},
            {'costo': 0.4, 'co2': 0.4, 'social': 0.2},
            {'costo': 0.3, 'co2': 0.5, 'social': 0.2},
            {'costo': 0.2, 'co2': 0.3, 'social': 0.5}
        ])
        
        resultados = []
        
        # Paralelizar diferentes combinaciones de pesos
        with ThreadPoolExecutor(max_workers=4) as executor:
            futuros = {
                executor.submit(
                    self.modelo.optimizar_multiobjetivo_ponderacion, 
                    pesos
                ): pesos for pesos in pesos_sets
            }
            
            for futuro in as_completed(futuros):
                pesos = futuros[futuro]
                try:
                    resultado = futuro.result()
                    resultado.pesos_utilizados = pesos
                    resultados.append(resultado)
                except Exception as e:
                    self.logger.warning(f"Error con pesos {pesos}: {str(e)}")
                    
        return {
            'metodo': 'ponderacion',
            'resultados': resultados,
            'pesos_evaluados': pesos_sets,
            'mejor_solucion': min(resultados, 
                                key=lambda x: x.costo_total + x.emisiones_co2) if resultados else None
        }
        
    def _optimizar_epsilon_restriccion(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Optimización por ε-restricción"""
        
        n_puntos = parametros.get('n_puntos', 20)
        objetivo_principal = parametros.get('objetivo_principal', 'costo')
        
        # Obtener rangos de objetivos
        min_costo = self.optimizar_objetivo_unico('costo')
        min_co2 = self.optimizar_objetivo_unico('co2')
        max_social = self.optimizar_objetivo_unico('social')
        
        # Generar frente Pareto
        frente_pareto = []
        
        if objetivo_principal == 'costo':
            # Variar restricción de CO2
            epsilons_co2 = np.linspace(min_co2.emisiones_co2, min_costo.emisiones_co2, n_puntos)
            
            for epsilon in epsilons_co2:
                try:
                    resultado = self.modelo._optimizar_con_restriccion_epsilon(
                        'costo', 'co2', epsilon
                    )
                    if resultado.estado_optimizacion == 'optimal':
                        frente_pareto.append([
                            resultado.costo_total,
                            resultado.emisiones_co2,
                            resultado.factor_social
                        ])
                except:
                    continue
                    
        return {
            'metodo': 'epsilon_restriccion',
            'frente_pareto': np.array(frente_pareto),
            'objetivo_principal': objetivo_principal,
            'n_puntos_generados': len(frente_pareto)
        }
        
    def _optimizar_topsis(self, parametros: Dict[str, Any]) -> Dict[str, Any]:
        """Optimización usando TOPSIS"""
        
        # Generar alternativas usando otros métodos
        alternativas = []
        
        # Agregar soluciones de objetivos únicos
        for objetivo in ['costo', 'co2', 'social']:
            resultado = self.optimizar_objetivo_unico(objetivo)
            if resultado.estado_optimizacion == 'optimal':
                alternativas.append(resultado)
                
        # Agregar soluciones de ponderación
        pesos_sets = [
            {'costo': 0.6, 'co2': 0.3, 'social': 0.1},
            {'costo': 0.3, 'co2': 0.5, 'social': 0.2},
            {'costo': 0.2, 'co2': 0.3, 'social': 0.5}
        ]
        
        for pesos in pesos_sets:
            resultado = self.modelo.optimizar_multiobjetivo_ponderacion(pesos)
            if resultado.estado_optimizacion == 'optimal':
                alternativas.append(resultado)
                
        if not alternativas:
            return {'error': 'No se encontraron soluciones válidas para TOPSIS'}
            
        # Aplicar TOPSIS
        topsis = AlgoritmoTOPSIS()
        
        # Construir matriz de decisión
        matriz_decision = []
        for alt in alternativas:
            matriz_decision.append([
                alt.costo_total,
                alt.emisiones_co2,
                alt.factor_social
            ])
            
        matriz_decision = np.array(matriz_decision)
        
        # Pesos y criterios
        pesos = parametros.get('pesos', [0.4, 0.4, 0.2])
        criterios = parametros.get('criterios', ['min', 'min', 'max'])
        
        ranking, scores = topsis.calcular_ranking(matriz_decision, pesos, criterios)
        
        return {
            'metodo': 'topsis',
            'alternativas': alternativas,
            'ranking': ranking,
            'scores': scores,
            'mejor_solucion': alternativas[ranking[0]],
            'matriz_decision': matriz_decision
        }
        
    def analisis_sensibilidad_completo(self, parametros: List[str] = None,
                                     variacion: float = 0.2,
                                     n_puntos: int = 11) -> Dict[str, pd.DataFrame]:
        """
        Análisis de sensibilidad completo para múltiples parámetros
        
        Args:
            parametros: Lista de parámetros a analizar
            variacion: Porcentaje de variación (±)
            n_puntos: Número de puntos por parámetro
            
        Returns:
            Diccionario con DataFrames de sensibilidad por parámetro
        """
        if parametros is None:
            parametros = ['costos', 'emisiones', 'factores_sociales']
            
        self.logger.info(f"Iniciando análisis de sensibilidad para {len(parametros)} parámetros")
        
        resultados_sensibilidad = {}
        
        for parametro in parametros:
            self.logger.info(f"Analizando sensibilidad de: {parametro}")
            
            try:
                df_sensibilidad = self.modelo.analisis_sensibilidad(
                    parametro, variacion, n_puntos
                )
                resultados_sensibilidad[parametro] = df_sensibilidad
                
            except Exception as e:
                self.logger.warning(f"Error en sensibilidad de {parametro}: {str(e)}")
                
        return resultados_sensibilidad
        
    def analisis_incertidumbre_montecarlo(self, n_simulaciones: int = 1000,
                                        parametros_inciertos: Dict[str, Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Análisis de incertidumbre usando simulación Monte Carlo
        
        Args:
            n_simulaciones: Número de simulaciones
            parametros_inciertos: Dict con parámetros y sus distribuciones
            
        Returns:
            Resultados del análisis de incertidumbre
        """
        return self.analizador_incertidumbre.simulacion_montecarlo(
            n_simulaciones, parametros_inciertos
        )
        
    def generar_frente_pareto_completo(self, metodos: List[str] = None,
                                     n_puntos: int = 50) -> np.ndarray:
        """
        Genera frente Pareto usando múltiples métodos
        
        Args:
            metodos: Lista de métodos a usar
            n_puntos: Número de puntos objetivo
            
        Returns:
            Array con frente Pareto combinado
        """
        if metodos is None:
            metodos = ['epsilon_restriccion', 'ponderacion']
            
        if self.frente_pareto_cache is not None:
            return self.frente_pareto_cache
            
        self.logger.info(f"Generando frente Pareto con métodos: {metodos}")
        
        puntos_pareto = []
        
        for metodo in metodos:
            try:
                if metodo == 'epsilon_restriccion':
                    frente = self.modelo.generar_frente_pareto(n_puntos)
                    if len(frente) > 0:
                        puntos_pareto.extend(frente.tolist())
                        
                elif metodo == 'ponderacion':
                    # Generar múltiples combinaciones de pesos
                    n_pesos = int(np.sqrt(n_puntos))
                    for i in range(n_pesos):
                        for j in range(n_pesos):
                            w1 = i / (n_pesos - 1)
                            w2 = j / (n_pesos - 1)
                            w3 = 1 - w1 - w2
                            
                            if w3 >= 0:
                                pesos = {'costo': w1, 'co2': w2, 'social': w3}
                                try:
                                    resultado = self.modelo.optimizar_multiobjetivo_ponderacion(pesos)
                                    if resultado.estado_optimizacion == 'optimal':
                                        puntos_pareto.append([
                                            resultado.costo_total,
                                            resultado.emisiones_co2,
                                            resultado.factor_social
                                        ])
                                except:
                                    continue
                                    
            except Exception as e:
                self.logger.warning(f"Error con método {metodo}: {str(e)}")
                
        if puntos_pareto:
            frente_completo = np.array(puntos_pareto)
            
            # Filtrar puntos dominados
            frente_filtrado = self._filtrar_dominados(frente_completo)
            
            self.frente_pareto_cache = frente_filtrado
            self.logger.info(f"Frente Pareto generado con {len(frente_filtrado)} puntos")
            
            return frente_filtrado
        else:
            self.logger.warning("No se pudieron generar puntos Pareto")
            return np.array([])
            
    def _filtrar_dominados(self, puntos: np.ndarray) -> np.ndarray:
        """Filtra puntos dominados del frente Pareto"""
        if len(puntos) == 0:
            return puntos
            
        # Convertir factor social a minimización (negativo)
        puntos_min = puntos.copy()
        puntos_min[:, 2] = -puntos_min[:, 2]
        
        # Encontrar puntos no dominados
        n_puntos = len(puntos_min)
        es_dominado = np.zeros(n_puntos, dtype=bool)
        
        for i in range(n_puntos):
            for j in range(n_puntos):
                if i != j and not es_dominado[i]:
                    # i es dominado por j si j es mejor o igual en todos los objetivos
                    # y estrictamente mejor en al menos uno
                    domina = np.all(puntos_min[j] <= puntos_min[i]) and \
                            np.any(puntos_min[j] < puntos_min[i])
                    if domina:
                        es_dominado[i] = True
                        break
                        
        return puntos[~es_dominado]
        
    def exportar_resultados_completos(self, archivo_base: str) -> None:
        """
        Exporta todos los resultados a múltiples archivos
        
        Args:
            archivo_base: Nombre base para los archivos (sin extensión)
        """
        self.logger.info(f"Exportando resultados completos a {archivo_base}")
        
        try:
            # 1. Exportar validación
            self.validador.exportar_validacion_excel(f"{archivo_base}_validacion.xlsx")
            
            # 2. Exportar frente Pareto
            if self.frente_pareto_cache is not None:
                df_pareto = pd.DataFrame(
                    self.frente_pareto_cache,
                    columns=['Costo', 'Emisiones_CO2', 'Factor_Social']
                )
                df_pareto.to_excel(f"{archivo_base}_pareto.xlsx", index=False)
                
            # 3. Exportar resultados individuales
            if self.resultados_cache:
                datos_resultados = []
                for metodo, resultado in self.resultados_cache.items():
                    datos_resultados.append({
                        'Metodo': metodo,
                        'Costo_Total': resultado.costo_total,
                        'Emisiones_CO2': resultado.emisiones_co2,
                        'Factor_Social': resultado.factor_social,
                        'Estado': resultado.estado_optimizacion,
                        'Tiempo_s': resultado.tiempo_solucion
                    })
                    
                df_resultados = pd.DataFrame(datos_resultados)
                df_resultados.to_excel(f"{archivo_base}_resultados.xlsx", index=False)
                
            # 4. Exportar parámetros del modelo
            self._exportar_parametros_modelo(f"{archivo_base}_modelo.xlsx")
            
            self.logger.info("Exportación completada exitosamente")
            
        except Exception as e:
            self.logger.error(f"Error en exportación: {str(e)}")
            
    def _exportar_parametros_modelo(self, archivo: str) -> None:
        """Exporta parámetros del modelo a Excel"""
        
        with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
            
            # Hoja 1: Recursos
            datos_recursos = []
            for nombre, recurso in self.modelo.recursos.items():
                datos_recursos.append({
                    'Nombre': nombre,
                    'Capacidad_Maxima': recurso.capacidad_maxima,
                    'Factor_Energia': recurso.factor_energia,
                    'Costo_Unitario': recurso.costo_unitario,
                    'Factor_Emision': recurso.factor_emision,
                    'Factor_Social': recurso.factor_social,
                    'Vida_Util': recurso.vida_util
                })
            df_recursos = pd.DataFrame(datos_recursos)
            df_recursos.to_excel(writer, sheet_name='Recursos', index=False)
            
            # Hoja 2: Tareas
            datos_tareas = []
            for nombre, tarea in self.modelo.tareas.items():
                datos_tareas.append({
                    'Nombre': nombre,
                    'Demanda_Anual': tarea.demanda_anual,
                    'Potencia_Maxima': tarea.potencia_maxima,
                    'Factor_Carga': tarea.factor_carga,
                    'Prioridad': tarea.prioridad
                })
            df_tareas = pd.DataFrame(datos_tareas)
            df_tareas.to_excel(writer, sheet_name='Tareas', index=False)
            
            # Hoja 3: Configuración general
            config_general = {
                'Parametro': [
                    'Horizonte_Temporal',
                    'Numero_Recursos',
                    'Numero_Tareas',
                    'Almacenamiento_Configurado'
                ],
                'Valor': [
                    self.modelo.horizonte_temporal,
                    len(self.modelo.recursos),
                    len(self.modelo.tareas),
                    self.modelo.almacenamiento_config is not None
                ]
            }
            df_config = pd.DataFrame(config_general)
            df_config.to_excel(writer, sheet_name='Configuracion', index=False)
            
    def _optimizar_con_scipy(self, objetivo: str) -> ResultadoOptimizacion:
        """Optimización usando scipy.optimize"""
        from scipy.optimize import minimize
        
        # Implementación simplificada usando scipy
        # En un caso real, aquí se definiría la función objetivo y restricciones
        
        def funcion_objetivo(x):
            # Placeholder - en implementación real se evaluaría el modelo
            return np.sum(x**2)
            
        n_vars = len(self.modelo.recursos) * len(self.modelo.tareas)
        x0 = np.ones(n_vars) * 0.1
        
        inicio = time.time()
        
        try:
            resultado_scipy = minimize(funcion_objetivo, x0, method='SLSQP')
            
            return ResultadoOptimizacion(
                asignaciones={},  # Placeholder
                costo_total=resultado_scipy.fun,
                emisiones_co2=0,  # Placeholder
                factor_social=0,  # Placeholder
                estado_optimizacion='optimal' if resultado_scipy.success else 'failed',
                tiempo_solucion=time.time() - inicio
            )
            
        except Exception as e:
            return ResultadoOptimizacion(
                asignaciones={},
                costo_total=float('inf'),
                emisiones_co2=float('inf'),
                factor_social=0,
                estado_optimizacion=f"Error scipy: {str(e)}",
                tiempo_solucion=time.time() - inicio
            )
            
    def _optimizar_con_pulp(self, objetivo: str) -> ResultadoOptimizacion:
        """Optimización usando PuLP"""
        try:
            import pulp as pl
        except ImportError:
            raise ImportError("PuLP no está instalado. Instalar con: pip install pulp")
            
        # Implementación simplificada usando PuLP
        # En un caso real, aquí se definiría el modelo completo de programación lineal
        
        inicio = time.time()
        
        try:
            # Crear problema
            prob = pl.LpProblem("Modelo_Energetico", pl.LpMinimize)
            
            # Variables (simplificado)
            recursos_nombres = list(self.modelo.recursos.keys())
            tareas_nombres = list(self.modelo.tareas.keys())
            
            variables = {}
            for i, recurso in enumerate(recursos_nombres):
                for j, tarea in enumerate(tareas_nombres):
                    var_name = f"x_{i}_{j}"
                    variables[var_name] = pl.LpVariable(var_name, lowBound=0)
                    
            # Función objetivo (simplificada)
            if objetivo == 'costo':
                objetivo_expr = pl.lpSum([
                    variables[f"x_{i}_{j}"] * self.modelo.recursos[recurso].costo_unitario
                    for i, recurso in enumerate(recursos_nombres)
                    for j, tarea in enumerate(tareas_nombres)
                ])
            else:
                # Placeholder para otros objetivos
                objetivo_expr = pl.lpSum(variables.values())
                
            prob += objetivo_expr
            
            # Restricciones (simplificadas)
            for j, tarea in enumerate(tareas_nombres):
                demanda_expr = pl.lpSum([
                    variables[f"x_{i}_{j}"]
                    for i in range(len(recursos_nombres))
                ])
                prob += demanda_expr >= self.modelo.tareas[tarea].demanda_anual / 1000  # Simplificado
                
            # Resolver
            prob.solve(pl.PULP_CBC_CMD(msg=0))
            
            # Extraer resultados
            estado = "optimal" if prob.status == pl.LpStatusOptimal else "failed"
            valor_objetivo = pl.value(prob.objective) if estado == "optimal" else float('inf')
            
            return ResultadoOptimizacion(
                asignaciones={},  # Placeholder - extraer de variables
                costo_total=valor_objetivo if objetivo == 'costo' else 0,
                emisiones_co2=valor_objetivo if objetivo == 'co2' else 0,
                factor_social=valor_objetivo if objetivo == 'social' else 0,
                estado_optimizacion=estado,
                tiempo_solucion=time.time() - inicio
            )
            
        except Exception as e:
            return ResultadoOptimizacion(
                asignaciones={},
                costo_total=float('inf'),
                emisiones_co2=float('inf'),
                factor_social=0,
                estado_optimizacion=f"Error PuLP: {str(e)}",
                tiempo_solucion=time.time() - inicio
            )
            
    def _convertir_individuo_a_resultado(self, individuo) -> ResultadoOptimizacion:
        """Convierte un individuo de algoritmo genético a ResultadoOptimizacion"""
        # Placeholder - implementar conversión real
        return ResultadoOptimizacion(
            asignaciones={},
            costo_total=individuo.fitness.values[0] if hasattr(individuo, 'fitness') else 0,
            emisiones_co2=individuo.fitness.values[1] if hasattr(individuo, 'fitness') else 0,
            factor_social=individuo.fitness.values[2] if hasattr(individuo, 'fitness') else 0,
            estado_optimizacion="optimal",
            tiempo_solucion=0
        )
        
    def obtener_resumen_optimizacion(self) -> Dict[str, Any]:
        """
        Obtiene resumen completo de todas las optimizaciones realizadas
        
        Returns:
            Diccionario con resumen de resultados
        """
        resumen = {
            'total_optimizaciones': len(self.resultados_cache),
            'metodos_utilizados': list(self.resultados_cache.keys()),
            'frente_pareto_puntos': len(self.frente_pareto_cache) if self.frente_pareto_cache is not None else 0,
            'mejor_costo': None,
            'menor_emisiones': None,
            'mayor_factor_social': None,
            'tiempo_total_optimizacion': 0
        }
        
        if self.resultados_cache:
            resultados_validos = [r for r in self.resultados_cache.values() 
                                if r.estado_optimizacion == 'optimal']
            
            if resultados_validos:
                resumen['mejor_costo'] = min(resultados_validos, key=lambda x: x.costo_total)
                resumen['menor_emisiones'] = min(resultados_validos, key=lambda x: x.emisiones_co2)
                resumen['mayor_factor_social'] = max(resultados_validos, key=lambda x: x.factor_social)
                resumen['tiempo_total_optimizacion'] = sum(r.tiempo_solucion for r in resultados_validos)
                
        return resumen
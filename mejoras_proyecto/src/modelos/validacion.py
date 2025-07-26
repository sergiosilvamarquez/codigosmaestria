"""
Módulo de validación y manejo de errores para el sistema energético
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
import warnings
from dataclasses import dataclass
from .modelo_energetico import ModeloEnergetico, RecursoEnergetico, Tarea

@dataclass
class ErrorValidacion:
    """Clase para representar errores de validación"""
    tipo: str
    severidad: str  # 'error', 'warning', 'info'
    mensaje: str
    sugerencia: Optional[str] = None
    parametro_afectado: Optional[str] = None

class ValidadorParametros:
    """
    Validador completo de parámetros y consistencia del modelo
    
    Características:
    - Validaciones de entrada exhaustivas
    - Detección de inconsistencias físicas
    - Análisis de factibilidad
    - Sugerencias de corrección automática
    """
    
    def __init__(self, modelo: ModeloEnergetico):
        """
        Inicializa el validador
        
        Args:
            modelo: Instancia del modelo energético a validar
        """
        self.modelo = modelo
        self.errores: List[ErrorValidacion] = []
        self.warnings: List[ErrorValidacion] = []
        self.tolerancia_numerica = 1e-6
        
    def validar_completo(self) -> Tuple[bool, List[ErrorValidacion]]:
        """
        Ejecuta validación completa del modelo
        
        Returns:
            Tuple (es_valido, lista_errores)
        """
        self.errores.clear()
        self.warnings.clear()
        
        # Validaciones básicas
        self._validar_estructura_basica()
        self._validar_recursos()
        self._validar_tareas()
        self._validar_consistencia_fisica()
        self._validar_factibilidad_energetica()
        self._validar_factibilidad_economica()
        self._validar_parametros_numericos()
        
        # Validaciones avanzadas
        self._validar_balance_energetico()
        self._validar_configuracion_almacenamiento()
        self._analizar_dimensionamiento()
        
        # Combinar errores y warnings
        todos_errores = self.errores + self.warnings
        es_valido = len(self.errores) == 0
        
        return es_valido, todos_errores
        
    def _validar_estructura_basica(self) -> None:
        """Valida estructura básica del modelo"""
        
        # Verificar que existan recursos
        if not self.modelo.recursos:
            self.errores.append(ErrorValidacion(
                tipo="estructura",
                severidad="error",
                mensaje="No se han definido recursos energéticos",
                sugerencia="Agregar al menos un recurso usando modelo.agregar_recurso()"
            ))
            
        # Verificar que existan tareas
        if not self.modelo.tareas:
            self.errores.append(ErrorValidacion(
                tipo="estructura",
                severidad="error",
                mensaje="No se han definido tareas/demandas",
                sugerencia="Agregar al menos una tarea usando modelo.agregar_tarea()"
            ))
            
        # Verificar horizonte temporal válido
        if self.modelo.horizonte_temporal <= 0:
            self.errores.append(ErrorValidacion(
                tipo="estructura",
                severidad="error",
                mensaje=f"Horizonte temporal inválido: {self.modelo.horizonte_temporal}",
                sugerencia="Usar horizonte temporal positivo (ej: 8760 para año completo)"
            ))
        elif self.modelo.horizonte_temporal > 8760 * 10:
            self.warnings.append(ErrorValidacion(
                tipo="estructura",
                severidad="warning",
                mensaje=f"Horizonte temporal muy largo: {self.modelo.horizonte_temporal} horas",
                sugerencia="Considerar reducir para mejorar tiempo de cómputo"
            ))
            
    def _validar_recursos(self) -> None:
        """Valida parámetros de recursos energéticos"""
        
        for nombre, recurso in self.modelo.recursos.items():
            
            # Capacidades positivas
            if recurso.capacidad_maxima <= 0:
                self.errores.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="error",
                    mensaje=f"Capacidad máxima inválida para {nombre}: {recurso.capacidad_maxima}",
                    parametro_afectado=nombre,
                    sugerencia="Usar capacidad positiva en kWh/año"
                ))
                
            # Factor de energía válido
            if recurso.factor_energia <= 0:
                self.errores.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="error",
                    mensaje=f"Factor de energía inválido para {nombre}: {recurso.factor_energia}",
                    parametro_afectado=nombre,
                    sugerencia="Usar factor de energía positivo"
                ))
            elif recurso.factor_energia > 1000:
                self.warnings.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="warning",
                    mensaje=f"Factor de energía muy alto para {nombre}: {recurso.factor_energia}",
                    parametro_afectado=nombre,
                    sugerencia="Verificar unidades (kWh/unidad)"
                ))
                
            # Costos válidos
            if recurso.costo_unitario < 0:
                self.errores.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="error",
                    mensaje=f"Costo unitario negativo para {nombre}: {recurso.costo_unitario}",
                    parametro_afectado=nombre,
                    sugerencia="Usar costo no negativo en $/kWh"
                ))
            elif recurso.costo_unitario > 1:
                self.warnings.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="warning",
                    mensaje=f"Costo unitario muy alto para {nombre}: ${recurso.costo_unitario}/kWh",
                    parametro_afectado=nombre,
                    sugerencia="Verificar unidades y valor de mercado"
                ))
                
            # Factor de emisión válido
            if recurso.factor_emision < 0:
                self.errores.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="error",
                    mensaje=f"Factor de emisión negativo para {nombre}: {recurso.factor_emision}",
                    parametro_afectado=nombre,
                    sugerencia="Usar factor no negativo en kgCO2/kWh"
                ))
            elif recurso.factor_emision > 2:
                self.warnings.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="warning",
                    mensaje=f"Factor de emisión muy alto para {nombre}: {recurso.factor_emision} kgCO2/kWh",
                    parametro_afectado=nombre,
                    sugerencia="Verificar valor típico para la tecnología"
                ))
                
            # Factor social válido
            if not (0 <= recurso.factor_social <= 1):
                self.errores.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="error",
                    mensaje=f"Factor social fuera de rango para {nombre}: {recurso.factor_social}",
                    parametro_afectado=nombre,
                    sugerencia="Usar valor entre 0 y 1"
                ))
                
            # Vida útil razonable
            if recurso.vida_util <= 0:
                self.errores.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="error",
                    mensaje=f"Vida útil inválida para {nombre}: {recurso.vida_util}",
                    parametro_afectado=nombre,
                    sugerencia="Usar vida útil positiva en años"
                ))
            elif recurso.vida_util > 100:
                self.warnings.append(ErrorValidacion(
                    tipo="recurso",
                    severidad="warning",
                    mensaje=f"Vida útil muy larga para {nombre}: {recurso.vida_util} años",
                    parametro_afectado=nombre,
                    sugerencia="Verificar valor típico para la tecnología"
                ))
                
            # Eficiencias válidas
            for tarea, eficiencia in recurso.eficiencia.items():
                if not (0 < eficiencia <= 1):
                    self.errores.append(ErrorValidacion(
                        tipo="recurso",
                        severidad="error",
                        mensaje=f"Eficiencia inválida {nombre}->{tarea}: {eficiencia}",
                        parametro_afectado=nombre,
                        sugerencia="Usar eficiencia entre 0 y 1"
                    ))
                    
            # Rampa válida si se especifica
            if recurso.rampa_maxima is not None:
                if recurso.rampa_maxima <= 0:
                    self.errores.append(ErrorValidacion(
                        tipo="recurso",
                        severidad="error",
                        mensaje=f"Rampa máxima inválida para {nombre}: {recurso.rampa_maxima}",
                        parametro_afectado=nombre,
                        sugerencia="Usar rampa positiva en kW/h"
                    ))
                    
    def _validar_tareas(self) -> None:
        """Valida parámetros de tareas/demandas"""
        
        for nombre, tarea in self.modelo.tareas.items():
            
            # Demanda anual positiva
            if tarea.demanda_anual <= 0:
                self.errores.append(ErrorValidacion(
                    tipo="tarea",
                    severidad="error",
                    mensaje=f"Demanda anual inválida para {nombre}: {tarea.demanda_anual}",
                    parametro_afectado=nombre,
                    sugerencia="Usar demanda positiva en kWh/año"
                ))
                
            # Potencia máxima consistente
            if tarea.potencia_maxima <= 0:
                self.errores.append(ErrorValidacion(
                    tipo="tarea",
                    severidad="error",
                    mensaje=f"Potencia máxima inválida para {nombre}: {tarea.potencia_maxima}",
                    parametro_afectado=nombre,
                    sugerencia="Usar potencia positiva en kW"
                ))
            else:
                # Verificar consistencia entre demanda anual y potencia máxima
                horas_equivalentes = tarea.demanda_anual / tarea.potencia_maxima
                if horas_equivalentes > self.modelo.horizonte_temporal:
                    self.warnings.append(ErrorValidacion(
                        tipo="tarea",
                        severidad="warning",
                        mensaje=f"Inconsistencia demanda/potencia para {nombre}: "
                               f"{horas_equivalentes:.1f} h equiv > {self.modelo.horizonte_temporal} h",
                        parametro_afectado=nombre,
                        sugerencia="Ajustar potencia máxima o demanda anual"
                    ))
                    
            # Factor de carga razonable
            if not (0 < tarea.factor_carga <= 1):
                self.errores.append(ErrorValidacion(
                    tipo="tarea",
                    severidad="error",
                    mensaje=f"Factor de carga inválido para {nombre}: {tarea.factor_carga}",
                    parametro_afectado=nombre,
                    sugerencia="Usar factor de carga entre 0 y 1"
                ))
                
            # Prioridad válida
            if tarea.prioridad not in [1, 2, 3]:
                self.warnings.append(ErrorValidacion(
                    tipo="tarea",
                    severidad="warning",
                    mensaje=f"Prioridad no estándar para {nombre}: {tarea.prioridad}",
                    parametro_afectado=nombre,
                    sugerencia="Usar prioridad 1=alta, 2=media, 3=baja"
                ))
                
            # Perfil temporal válido si se especifica
            if tarea.perfil_temporal is not None:
                if len(tarea.perfil_temporal) not in [24, 8760]:
                    self.warnings.append(ErrorValidacion(
                        tipo="tarea",
                        severidad="warning",
                        mensaje=f"Longitud de perfil temporal no estándar para {nombre}: {len(tarea.perfil_temporal)}",
                        parametro_afectado=nombre,
                        sugerencia="Usar 24 puntos (horario) o 8760 (anual)"
                    ))
                    
                # Verificar que sume aproximadamente a 1 (normalizado)
                suma_perfil = np.sum(tarea.perfil_temporal)
                if not np.isclose(suma_perfil, 1.0, rtol=0.01):
                    self.warnings.append(ErrorValidacion(
                        tipo="tarea",
                        severidad="warning",
                        mensaje=f"Perfil temporal no normalizado para {nombre}: suma={suma_perfil:.3f}",
                        parametro_afectado=nombre,
                        sugerencia="Normalizar perfil para que sume 1.0"
                    ))
                    
    def _validar_consistencia_fisica(self) -> None:
        """Valida consistencia física entre recursos y tareas"""
        
        # Verificar que las eficiencias de recursos cubran todas las tareas
        for nombre_recurso, recurso in self.modelo.recursos.items():
            tareas_faltantes = set(self.modelo.tareas.keys()) - set(recurso.eficiencia.keys())
            if tareas_faltantes:
                self.warnings.append(ErrorValidacion(
                    tipo="consistencia",
                    severidad="warning",
                    mensaje=f"Recurso {nombre_recurso} no tiene eficiencia definida para: {tareas_faltantes}",
                    parametro_afectado=nombre_recurso,
                    sugerencia="Definir eficiencias para todas las tareas o usar valor por defecto"
                ))
                
        # Verificar factibilidad temporal básica
        for nombre_tarea, tarea in self.modelo.tareas.items():
            if tarea.perfil_temporal is not None:
                pico_perfil = np.max(tarea.perfil_temporal)
                potencia_pico_teorica = tarea.demanda_anual * pico_perfil * len(tarea.perfil_temporal)
                
                if potencia_pico_teorica > tarea.potencia_maxima * 1.1:  # 10% tolerancia
                    self.warnings.append(ErrorValidacion(
                        tipo="consistencia",
                        severidad="warning",
                        mensaje=f"Perfil temporal inconsistente para {nombre_tarea}: "
                               f"pico teórico {potencia_pico_teorica:.1f} kW > {tarea.potencia_maxima} kW",
                        parametro_afectado=nombre_tarea,
                        sugerencia="Ajustar perfil temporal o potencia máxima"
                    ))
                    
    def _validar_factibilidad_energetica(self) -> None:
        """Valida factibilidad energética del sistema"""
        
        # Calcular oferta total de energía
        oferta_total = 0
        for recurso in self.modelo.recursos.values():
            # Asumiendo factor de capacidad promedio de 0.5 si no se especifica
            factor_capacidad = getattr(recurso, 'factor_capacidad', 0.5)
            oferta_total += recurso.capacidad_maxima * factor_capacidad
            
        # Calcular demanda total
        demanda_total = sum(tarea.demanda_anual for tarea in self.modelo.tareas.values())
        
        # Verificar balance básico
        if demanda_total > oferta_total:
            self.errores.append(ErrorValidacion(
                tipo="factibilidad",
                severidad="error",
                mensaje=f"Demanda total ({demanda_total:.1f} kWh/año) > Oferta total ({oferta_total:.1f} kWh/año)",
                sugerencia="Aumentar capacidad de recursos o reducir demandas"
            ))
        elif demanda_total < oferta_total * 0.1:
            self.warnings.append(ErrorValidacion(
                tipo="factibilidad",
                severidad="warning",
                mensaje=f"Oferta muy superior a demanda: {oferta_total/demanda_total:.1f}x",
                sugerencia="Considerar reducir capacidades para optimizar costos"
            ))
            
        # Verificar balance por eficiencias
        for nombre_tarea, tarea in self.modelo.tareas.items():
            oferta_tarea = 0
            for recurso in self.modelo.recursos.values():
                eficiencia = recurso.eficiencia.get(nombre_tarea, 0)
                factor_capacidad = getattr(recurso, 'factor_capacidad', 0.5)
                oferta_tarea += (recurso.capacidad_maxima * factor_capacidad * 
                               recurso.factor_energia * eficiencia)
                
            if tarea.demanda_anual > oferta_tarea:
                self.warnings.append(ErrorValidacion(
                    tipo="factibilidad",
                    severidad="warning",
                    mensaje=f"Posible déficit para tarea {nombre_tarea}: "
                           f"demanda {tarea.demanda_anual:.1f} > oferta {oferta_tarea:.1f} kWh/año",
                    parametro_afectado=nombre_tarea,
                    sugerencia="Verificar capacidades y eficiencias"
                ))
                
    def _validar_factibilidad_economica(self) -> None:
        """Valida factibilidad económica básica"""
        
        # Estimar costos mínimos
        costo_minimo = 0
        for recurso in self.modelo.recursos.values():
            # Costo operativo anualizado mínimo
            factor_capacidad = getattr(recurso, 'factor_capacidad', 0.5)
            energia_anual = recurso.capacidad_maxima * factor_capacidad
            costo_minimo += energia_anual * recurso.costo_unitario
            
        # Estimar costos máximos (operación a plena capacidad)
        costo_maximo = 0
        for recurso in self.modelo.recursos.values():
            energia_anual = recurso.capacidad_maxima
            costo_maximo += energia_anual * recurso.costo_unitario
            
        if costo_minimo > 1e9:  # $1B threshold
            self.warnings.append(ErrorValidacion(
                tipo="economia",
                severidad="warning",
                mensaje=f"Costos estimados muy altos: ${costo_minimo/1e6:.1f}M - ${costo_maximo/1e6:.1f}M",
                sugerencia="Verificar parámetros de costo y capacidades"
            ))
            
    def _validar_parametros_numericos(self) -> None:
        """Valida estabilidad numérica de parámetros"""
        
        # Verificar rangos de valores para estabilidad numérica
        for nombre, recurso in self.modelo.recursos.items():
            # Capacidades muy pequeñas pueden causar problemas numéricos
            if recurso.capacidad_maxima < 1e-3:
                self.warnings.append(ErrorValidacion(
                    tipo="numerico",
                    severidad="warning",
                    mensaje=f"Capacidad muy pequeña para {nombre}: {recurso.capacidad_maxima}",
                    parametro_afectado=nombre,
                    sugerencia="Usar unidades más apropiadas o valores mayores"
                ))
                
            # Costos muy pequeños pueden causar problemas
            if 0 < recurso.costo_unitario < 1e-6:
                self.warnings.append(ErrorValidacion(
                    tipo="numerico",
                    severidad="warning",
                    mensaje=f"Costo unitario muy pequeño para {nombre}: {recurso.costo_unitario}",
                    parametro_afectado=nombre,
                    sugerencia="Verificar unidades de costo"
                ))
                
        # Verificar condicionamiento de matriz implícita
        capacidades = np.array([r.capacidad_maxima for r in self.modelo.recursos.values()])
        demandas = np.array([t.demanda_anual for t in self.modelo.tareas.values()])
        
        if len(capacidades) > 0 and len(demandas) > 0:
            ratio_max_min_cap = np.max(capacidades) / (np.min(capacidades) + 1e-12)
            ratio_max_min_dem = np.max(demandas) / (np.min(demandas) + 1e-12)
            
            if ratio_max_min_cap > 1e6:
                self.warnings.append(ErrorValidacion(
                    tipo="numerico",
                    severidad="warning",
                    mensaje=f"Gran disparidad en capacidades: ratio {ratio_max_min_cap:.1e}",
                    sugerencia="Normalizar capacidades para mejor condicionamiento numérico"
                ))
                
            if ratio_max_min_dem > 1e6:
                self.warnings.append(ErrorValidacion(
                    tipo="numerico",
                    severidad="warning",
                    mensaje=f"Gran disparidad en demandas: ratio {ratio_max_min_dem:.1e}",
                    sugerencia="Normalizar demandas para mejor condicionamiento numérico"
                ))
                
    def _validar_balance_energetico(self) -> None:
        """Valida factibilidad del balance energético detallado"""
        
        if not self.modelo.recursos or not self.modelo.tareas:
            return
            
        # Crear matriz de eficiencias
        recursos_nombres = list(self.modelo.recursos.keys())
        tareas_nombres = list(self.modelo.tareas.keys())
        
        matriz_eficiencias = np.zeros((len(recursos_nombres), len(tareas_nombres)))
        capacidades = np.zeros(len(recursos_nombres))
        demandas = np.zeros(len(tareas_nombres))
        
        for i, nombre_recurso in enumerate(recursos_nombres):
            recurso = self.modelo.recursos[nombre_recurso]
            capacidades[i] = recurso.capacidad_maxima * recurso.factor_energia
            
            for j, nombre_tarea in enumerate(tareas_nombres):
                eficiencia = recurso.eficiencia.get(nombre_tarea, 0)
                matriz_eficiencias[i, j] = eficiencia
                
        for j, nombre_tarea in enumerate(tareas_nombres):
            demandas[j] = self.modelo.tareas[nombre_tarea].demanda_anual
            
        # Verificar si el sistema es factible usando programación lineal simple
        try:
            # Resolver max sum(eficiencia * uso) sujeto a capacidades
            oferta_maxima_por_tarea = np.zeros(len(tareas_nombres))
            
            for j in range(len(tareas_nombres)):
                # Para cada tarea, calcular máxima oferta posible
                oferta_maxima_por_tarea[j] = np.sum(capacidades * matriz_eficiencias[:, j])
                
                if demandas[j] > oferta_maxima_por_tarea[j] * 1.01:  # 1% tolerancia
                    self.errores.append(ErrorValidacion(
                        tipo="balance",
                        severidad="error",
                        mensaje=f"Imposible satisfacer demanda de {tareas_nombres[j]}: "
                               f"requiere {demandas[j]:.1f} kWh/año, máximo disponible {oferta_maxima_por_tarea[j]:.1f}",
                        parametro_afectado=tareas_nombres[j],
                        sugerencia="Aumentar capacidades de recursos compatibles o reducir demanda"
                    ))
                    
        except Exception as e:
            self.warnings.append(ErrorValidacion(
                tipo="balance",
                severidad="warning",
                mensaje=f"No se pudo verificar balance energético completamente: {str(e)}",
                sugerencia="Verificar manualmente factibilidad energética"
            ))
            
    def _validar_configuracion_almacenamiento(self) -> None:
        """Valida configuración de almacenamiento si existe"""
        
        if self.modelo.almacenamiento_config is None:
            return
            
        config = self.modelo.almacenamiento_config
        
        # Capacidad positiva
        if config['capacidad'] <= 0:
            self.errores.append(ErrorValidacion(
                tipo="almacenamiento",
                severidad="error",
                mensaje=f"Capacidad de almacenamiento inválida: {config['capacidad']}",
                sugerencia="Usar capacidad positiva en kWh"
            ))
            
        # Eficiencia válida
        if not (0 < config['eficiencia'] <= 1):
            self.errores.append(ErrorValidacion(
                tipo="almacenamiento",
                severidad="error",
                mensaje=f"Eficiencia de almacenamiento inválida: {config['eficiencia']}",
                sugerencia="Usar eficiencia entre 0 y 1"
            ))
            
        # Autodescarga válida
        if not (0 <= config['autodescarga'] < 1):
            self.errores.append(ErrorValidacion(
                tipo="almacenamiento",
                severidad="error",
                mensaje=f"Autodescarga inválida: {config['autodescarga']}",
                sugerencia="Usar valor entre 0 y 1 (fracción por hora)"
            ))
        elif config['autodescarga'] > 0.1:
            self.warnings.append(ErrorValidacion(
                tipo="almacenamiento",
                severidad="warning",
                mensaje=f"Autodescarga muy alta: {config['autodescarga']*100:.1f}%/hora",
                sugerencia="Verificar valor típico para la tecnología"
            ))
            
    def _analizar_dimensionamiento(self) -> None:
        """Analiza el dimensionamiento del sistema"""
        
        if not self.modelo.recursos or not self.modelo.tareas:
            return
            
        # Analizar sobredimensionamiento
        capacidad_total = sum(r.capacidad_maxima for r in self.modelo.recursos.values())
        demanda_total = sum(t.demanda_anual for t in self.modelo.tareas.values())
        
        if capacidad_total > demanda_total * 5:
            self.warnings.append(ErrorValidacion(
                tipo="dimensionamiento",
                severidad="warning",
                mensaje=f"Posible sobredimensionamiento: capacidad {capacidad_total/demanda_total:.1f}x demanda",
                sugerencia="Revisar si las capacidades son apropiadas"
            ))
            
        # Analizar diversificación de tecnologías
        if len(self.modelo.recursos) == 1:
            self.warnings.append(ErrorValidacion(
                tipo="dimensionamiento",
                severidad="warning",
                mensaje="Sistema con una sola tecnología",
                sugerencia="Considerar diversificación para mayor robustez"
            ))
            
        # Analizar balance de renovables vs convencionales
        renovables = ['solar', 'eolica', 'hidro', 'biogas']
        cap_renovable = 0
        cap_convencional = 0
        
        for nombre, recurso in self.modelo.recursos.items():
            es_renovable = any(tech in nombre.lower() for tech in renovables)
            if es_renovable:
                cap_renovable += recurso.capacidad_maxima
            else:
                cap_convencional += recurso.capacidad_maxima
                
        if cap_renovable + cap_convencional > 0:
            fraccion_renovable = cap_renovable / (cap_renovable + cap_convencional)
            if fraccion_renovable < 0.3:
                self.warnings.append(ErrorValidacion(
                    tipo="dimensionamiento",
                    severidad="info",
                    mensaje=f"Baja participación renovable: {fraccion_renovable*100:.1f}%",
                    sugerencia="Considerar aumentar energías renovables para mayor sustentabilidad"
                ))
                
    def generar_reporte_validacion(self) -> str:
        """
        Genera reporte textual de validación
        
        Returns:
            String con reporte formateado
        """
        reporte = []
        reporte.append("="*60)
        reporte.append("REPORTE DE VALIDACIÓN DEL MODELO ENERGÉTICO")
        reporte.append("="*60)
        
        # Resumen
        n_errores = len(self.errores)
        n_warnings = len(self.warnings)
        estado = "✓ VÁLIDO" if n_errores == 0 else "✗ CON ERRORES"
        
        reporte.append(f"\nEstado del modelo: {estado}")
        reporte.append(f"Errores críticos: {n_errores}")
        reporte.append(f"Advertencias: {n_warnings}")
        
        # Detalles de errores
        if self.errores:
            reporte.append("\n" + "="*40)
            reporte.append("ERRORES CRÍTICOS")
            reporte.append("="*40)
            
            for error in self.errores:
                reporte.append(f"\n🔴 {error.tipo.upper()}: {error.mensaje}")
                if error.parametro_afectado:
                    reporte.append(f"   Parámetro: {error.parametro_afectado}")
                if error.sugerencia:
                    reporte.append(f"   Sugerencia: {error.sugerencia}")
                    
        # Detalles de warnings
        if self.warnings:
            reporte.append("\n" + "="*40)
            reporte.append("ADVERTENCIAS")
            reporte.append("="*40)
            
            for warning in self.warnings:
                icon = "🟡" if warning.severidad == "warning" else "🔵"
                reporte.append(f"\n{icon} {warning.tipo.upper()}: {warning.mensaje}")
                if warning.parametro_afectado:
                    reporte.append(f"   Parámetro: {warning.parametro_afectado}")
                if warning.sugerencia:
                    reporte.append(f"   Sugerencia: {warning.sugerencia}")
                    
        # Estadísticas del modelo
        reporte.append("\n" + "="*40)
        reporte.append("ESTADÍSTICAS DEL MODELO")
        reporte.append("="*40)
        
        reporte.append(f"Recursos definidos: {len(self.modelo.recursos)}")
        reporte.append(f"Tareas definidas: {len(self.modelo.tareas)}")
        reporte.append(f"Horizonte temporal: {self.modelo.horizonte_temporal} horas")
        
        if self.modelo.recursos:
            cap_total = sum(r.capacidad_maxima for r in self.modelo.recursos.values())
            reporte.append(f"Capacidad total: {cap_total:,.1f} kWh/año")
            
        if self.modelo.tareas:
            dem_total = sum(t.demanda_anual for t in self.modelo.tareas.values())
            reporte.append(f"Demanda total: {dem_total:,.1f} kWh/año")
            
        if self.modelo.almacenamiento_config:
            cap_almacen = self.modelo.almacenamiento_config['capacidad']
            reporte.append(f"Almacenamiento configurado: {cap_almacen:.1f} kWh")
            
        reporte.append("\n" + "="*60)
        
        return "\n".join(reporte)
        
    def exportar_validacion_excel(self, archivo: str) -> None:
        """Exporta resultados de validación a Excel"""
        
        # Preparar datos para Excel
        datos_errores = []
        for error in self.errores + self.warnings:
            datos_errores.append({
                'Tipo': error.tipo,
                'Severidad': error.severidad,
                'Mensaje': error.mensaje,
                'Parámetro': error.parametro_afectado or '',
                'Sugerencia': error.sugerencia or ''
            })
            
        df_errores = pd.DataFrame(datos_errores)
        
        # Estadísticas del modelo
        estadisticas = {
            'Métrica': [
                'Número de recursos',
                'Número de tareas',
                'Horizonte temporal (h)',
                'Capacidad total (kWh/año)',
                'Demanda total (kWh/año)',
                'Errores críticos',
                'Advertencias'
            ],
            'Valor': [
                len(self.modelo.recursos),
                len(self.modelo.tareas),
                self.modelo.horizonte_temporal,
                sum(r.capacidad_maxima for r in self.modelo.recursos.values()) if self.modelo.recursos else 0,
                sum(t.demanda_anual for t in self.modelo.tareas.values()) if self.modelo.tareas else 0,
                len(self.errores),
                len(self.warnings)
            ]
        }
        df_estadisticas = pd.DataFrame(estadisticas)
        
        # Exportar a Excel
        with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
            df_errores.to_excel(writer, sheet_name='Validacion', index=False)
            df_estadisticas.to_excel(writer, sheet_name='Estadisticas', index=False)
            
    def corregir_automaticamente(self) -> List[str]:
        """
        Intenta corregir automáticamente errores simples
        
        Returns:
            Lista de correcciones aplicadas
        """
        correcciones = []
        
        for error in self.errores.copy():
            correccion_aplicada = None
            
            # Corrección de capacidades negativas o cero
            if error.tipo == "recurso" and "capacidad máxima inválida" in error.mensaje:
                if error.parametro_afectado in self.modelo.recursos:
                    recurso = self.modelo.recursos[error.parametro_afectado]
                    if recurso.capacidad_maxima <= 0:
                        recurso.capacidad_maxima = 1000.0  # Valor por defecto
                        correccion_aplicada = f"Capacidad de {error.parametro_afectado} corregida a 1000 kWh/año"
                        
            # Corrección de factores fuera de rango
            elif error.tipo == "recurso" and "factor social fuera de rango" in error.mensaje:
                if error.parametro_afectado in self.modelo.recursos:
                    recurso = self.modelo.recursos[error.parametro_afectado]
                    recurso.factor_social = np.clip(recurso.factor_social, 0, 1)
                    correccion_aplicada = f"Factor social de {error.parametro_afectado} ajustado al rango [0,1]"
                    
            # Corrección de eficiencias inválidas
            elif error.tipo == "recurso" and "eficiencia inválida" in error.mensaje:
                if error.parametro_afectado in self.modelo.recursos:
                    recurso = self.modelo.recursos[error.parametro_afectado]
                    for tarea, eficiencia in recurso.eficiencia.items():
                        if not (0 < eficiencia <= 1):
                            recurso.eficiencia[tarea] = 0.8  # Valor por defecto
                    correccion_aplicada = f"Eficiencias de {error.parametro_afectado} corregidas"
                    
            if correccion_aplicada:
                correcciones.append(correccion_aplicada)
                self.errores.remove(error)
                
        return correcciones
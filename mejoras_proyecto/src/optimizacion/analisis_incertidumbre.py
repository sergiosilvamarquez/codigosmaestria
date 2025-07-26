"""
Análisis de incertidumbre y simulación Monte Carlo
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import logging

class AnalizadorIncertidumbre:
    """
    Analizador de incertidumbre para sistemas energéticos
    
    Incluye:
    - Simulación Monte Carlo
    - Análisis de sensibilidad global
    - Propagación de incertidumbre
    """
    
    def __init__(self, modelo):
        """
        Inicializa el analizador
        
        Args:
            modelo: Modelo energético base
        """
        self.modelo = modelo
        self.logger = logging.getLogger(__name__)
        
    def simulacion_montecarlo(self, n_simulaciones: int = 1000,
                             parametros_inciertos: Optional[Dict[str, Dict[str, float]]] = None,
                             semilla: Optional[int] = None) -> Dict[str, Any]:
        """
        Realiza simulación Monte Carlo
        
        Args:
            n_simulaciones: Número de simulaciones
            parametros_inciertos: Dict con parámetros inciertos y sus distribuciones
            semilla: Semilla para reproducibilidad
            
        Returns:
            Diccionario con resultados estadísticos
        """
        
        if semilla is not None:
            np.random.seed(semilla)
            
        if parametros_inciertos is None:
            parametros_inciertos = self._obtener_parametros_inciertos_por_defecto()
            
        self.logger.info(f"Iniciando simulación Monte Carlo con {n_simulaciones} simulaciones")
        
        resultados = {
            'costos': [],
            'emisiones_co2': [],
            'factores_sociales': [],
            'estados_optimizacion': []
        }
        
        # Ejecutar simulaciones
        for i in range(n_simulaciones):
            if i % 100 == 0:
                self.logger.info(f"Simulación {i}/{n_simulaciones}")
                
            try:
                # Perturbar parámetros
                self._perturbar_parametros(parametros_inciertos)
                
                # Optimizar modelo perturbado
                resultado = self.modelo.optimizar_objetivo_unico('costo')
                
                # Almacenar resultados
                resultados['costos'].append(resultado.costo_total)
                resultados['emisiones_co2'].append(resultado.emisiones_co2)
                resultados['factores_sociales'].append(resultado.factor_social)
                resultados['estados_optimizacion'].append(resultado.estado_optimizacion)
                
                # Restaurar parámetros originales
                self._restaurar_parametros_originales()
                
            except Exception as e:
                self.logger.warning(f"Error en simulación {i}: {str(e)}")
                # Agregar valores por defecto para mantener consistencia
                resultados['costos'].append(np.nan)
                resultados['emisiones_co2'].append(np.nan)
                resultados['factores_sociales'].append(np.nan)
                resultados['estados_optimizacion'].append('error')
                
        # Calcular estadísticas
        estadisticas = self._calcular_estadisticas_montecarlo(resultados)
        
        # Análisis adicional
        analisis_adicional = self._analisis_adicional_montecarlo(resultados)
        
        return {
            'parametros_configuracion': {
                'n_simulaciones': n_simulaciones,
                'parametros_inciertos': parametros_inciertos,
                'semilla': semilla
            },
            'resultados_brutos': resultados,
            'estadisticas': estadisticas,
            'analisis': analisis_adicional
        }
        
    def _obtener_parametros_inciertos_por_defecto(self) -> Dict[str, Dict[str, float]]:
        """Define parámetros inciertos por defecto"""
        
        return {
            'costos_unitarios': {
                'distribucion': 'normal',
                'variabilidad': 0.15  # ±15% de variabilidad
            },
            'factores_emision': {
                'distribucion': 'normal', 
                'variabilidad': 0.10  # ±10% de variabilidad
            },
            'factores_sociales': {
                'distribucion': 'triangular',
                'variabilidad': 0.20  # ±20% de variabilidad
            },
            'demandas': {
                'distribucion': 'lognormal',
                'variabilidad': 0.25  # ±25% de variabilidad
            }
        }
        
    def _perturbar_parametros(self, parametros_inciertos: Dict[str, Dict[str, float]]) -> None:
        """Perturba los parámetros del modelo según las distribuciones especificadas"""
        
        # Guardar valores originales si no se han guardado
        if not hasattr(self, '_parametros_originales'):
            self._guardar_parametros_originales()
            
        # Perturbar costos unitarios
        if 'costos_unitarios' in parametros_inciertos:
            config = parametros_inciertos['costos_unitarios']
            for nombre, recurso in self.modelo.recursos.items():
                factor = self._generar_factor_aleatorio(config)
                recurso.costo_unitario = self._parametros_originales['costos'][nombre] * factor
                
        # Perturbar factores de emisión
        if 'factores_emision' in parametros_inciertos:
            config = parametros_inciertos['factores_emision']
            for nombre, recurso in self.modelo.recursos.items():
                factor = self._generar_factor_aleatorio(config)
                recurso.factor_emision = self._parametros_originales['emisiones'][nombre] * factor
                
        # Perturbar factores sociales
        if 'factores_sociales' in parametros_inciertos:
            config = parametros_inciertos['factores_sociales']
            for nombre, recurso in self.modelo.recursos.items():
                factor = self._generar_factor_aleatorio(config)
                recurso.factor_social = np.clip(
                    self._parametros_originales['sociales'][nombre] * factor, 0, 1
                )
                
        # Perturbar demandas
        if 'demandas' in parametros_inciertos:
            config = parametros_inciertos['demandas']
            for nombre, tarea in self.modelo.tareas.items():
                factor = self._generar_factor_aleatorio(config)
                tarea.demanda_anual = self._parametros_originales['demandas'][nombre] * factor
                
    def _generar_factor_aleatorio(self, config: Dict[str, Any]) -> float:
        """Genera factor aleatorio según distribución especificada"""
        
        distribucion = config.get('distribucion', 'normal')
        variabilidad = config.get('variabilidad', 0.1)
        
        if distribucion == 'normal':
            # Media = 1, desviación estándar = variabilidad
            return np.random.normal(1.0, variabilidad)
            
        elif distribucion == 'triangular':
            # Distribución triangular centrada en 1
            a = 1 - variabilidad
            b = 1 + variabilidad
            c = 1.0  # moda
            return np.random.triangular(a, c, b)
            
        elif distribucion == 'lognormal':
            # Distribución lognormal con media aproximada = 1
            sigma = variabilidad
            mu = -0.5 * sigma**2  # Para que la media sea aproximadamente 1
            return np.random.lognormal(mu, sigma)
            
        elif distribucion == 'uniforme':
            # Distribución uniforme
            a = 1 - variabilidad
            b = 1 + variabilidad
            return np.random.uniform(a, b)
            
        else:
            # Por defecto, normal
            return np.random.normal(1.0, variabilidad)
            
    def _guardar_parametros_originales(self) -> None:
        """Guarda los parámetros originales del modelo"""
        
        self._parametros_originales = {
            'costos': {},
            'emisiones': {},
            'sociales': {},
            'demandas': {}
        }
        
        # Guardar parámetros de recursos
        for nombre, recurso in self.modelo.recursos.items():
            self._parametros_originales['costos'][nombre] = recurso.costo_unitario
            self._parametros_originales['emisiones'][nombre] = recurso.factor_emision
            self._parametros_originales['sociales'][nombre] = recurso.factor_social
            
        # Guardar parámetros de tareas
        for nombre, tarea in self.modelo.tareas.items():
            self._parametros_originales['demandas'][nombre] = tarea.demanda_anual
            
    def _restaurar_parametros_originales(self) -> None:
        """Restaura los parámetros originales del modelo"""
        
        if not hasattr(self, '_parametros_originales'):
            return
            
        # Restaurar parámetros de recursos
        for nombre, recurso in self.modelo.recursos.items():
            if nombre in self._parametros_originales['costos']:
                recurso.costo_unitario = self._parametros_originales['costos'][nombre]
                recurso.factor_emision = self._parametros_originales['emisiones'][nombre]
                recurso.factor_social = self._parametros_originales['sociales'][nombre]
                
        # Restaurar parámetros de tareas  
        for nombre, tarea in self.modelo.tareas.items():
            if nombre in self._parametros_originales['demandas']:
                tarea.demanda_anual = self._parametros_originales['demandas'][nombre]
                
    def _calcular_estadisticas_montecarlo(self, resultados: Dict[str, List]) -> Dict[str, Any]:
        """Calcula estadísticas descriptivas de los resultados Monte Carlo"""
        
        estadisticas = {}
        
        for variable, valores in resultados.items():
            if variable == 'estados_optimizacion':
                # Estadísticas para variable categórica
                estados_unicos, cuentas = np.unique(valores, return_counts=True)
                estadisticas[variable] = {
                    'estados': estados_unicos.tolist(),
                    'frecuencias': cuentas.tolist(),
                    'tasa_exito': np.sum(np.array(valores) == 'optimal') / len(valores)
                }
            else:
                # Estadísticas para variables numéricas
                valores_numericos = [v for v in valores if not np.isnan(v)]
                
                if valores_numericos:
                    estadisticas[variable] = {
                        'media': np.mean(valores_numericos),
                        'mediana': np.median(valores_numericos),
                        'desv_estandar': np.std(valores_numericos),
                        'minimo': np.min(valores_numericos),
                        'maximo': np.max(valores_numericos),
                        'percentil_5': np.percentile(valores_numericos, 5),
                        'percentil_25': np.percentile(valores_numericos, 25),
                        'percentil_75': np.percentile(valores_numericos, 75),
                        'percentil_95': np.percentile(valores_numericos, 95),
                        'coef_variacion': np.std(valores_numericos) / np.mean(valores_numericos),
                        'n_validos': len(valores_numericos),
                        'n_nulos': len(valores) - len(valores_numericos)
                    }
                else:
                    estadisticas[variable] = {'error': 'No hay valores válidos'}
                    
        return estadisticas
        
    def _analisis_adicional_montecarlo(self, resultados: Dict[str, List]) -> Dict[str, Any]:
        """Realiza análisis adicional de los resultados Monte Carlo"""
        
        analisis = {}
        
        # Análisis de correlaciones
        df_resultados = pd.DataFrame({
            k: v for k, v in resultados.items() 
            if k != 'estados_optimizacion'
        })
        
        # Eliminar valores NaN para correlaciones
        df_limpio = df_resultados.dropna()
        
        if len(df_limpio) > 1:
            correlaciones = df_limpio.corr()
            analisis['correlaciones'] = correlaciones.to_dict()
        else:
            analisis['correlaciones'] = {'error': 'Datos insuficientes para correlaciones'}
            
        # Análisis de riesgo (probabilidades)
        costos_validos = [c for c in resultados['costos'] if not np.isnan(c)]
        emisiones_validas = [e for e in resultados['emisiones_co2'] if not np.isnan(e)]
        
        if costos_validos:
            media_costos = np.mean(costos_validos)
            analisis['riesgo'] = {
                'prob_costo_alto': np.sum(np.array(costos_validos) > media_costos * 1.2) / len(costos_validos),
                'prob_emisiones_altas': np.sum(np.array(emisiones_validas) > np.mean(emisiones_validas) * 1.2) / len(emisiones_validas) if emisiones_validas else 0,
                'var_at_risk_95': np.percentile(costos_validos, 95) if costos_validos else None
            }
            
        # Análisis de sensibilidad simplificado
        analisis['sensibilidad'] = self._analisis_sensibilidad_simplificado(df_limpio)
        
        return analisis
        
    def _analisis_sensibilidad_simplificado(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Análisis de sensibilidad simplificado basado en varianzas"""
        
        if df.empty or len(df.columns) < 2:
            return {'error': 'Datos insuficientes para análisis de sensibilidad'}
            
        # Calcular contribución de cada variable a la varianza total
        varianzas = df.var()
        varianza_total = varianzas.sum()
        
        if varianza_total > 0:
            contribuciones = (varianzas / varianza_total).to_dict()
        else:
            contribuciones = {col: 0 for col in df.columns}
            
        return {
            'contribuciones_varianza': contribuciones,
            'variable_mas_sensible': max(contribuciones.items(), key=lambda x: x[1])[0] if contribuciones else None
        }
        
    def analisis_escenarios(self, escenarios: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Analiza escenarios específicos (determinísticos)
        
        Args:
            escenarios: Dict con escenarios y factores de cambio
            
        Returns:
            Resultados por escenario
        """
        
        self.logger.info(f"Analizando {len(escenarios)} escenarios")
        
        # Guardar estado original
        if not hasattr(self, '_parametros_originales'):
            self._guardar_parametros_originales()
            
        resultados_escenarios = {}
        
        for nombre_escenario, factores in escenarios.items():
            self.logger.info(f"Evaluando escenario: {nombre_escenario}")
            
            try:
                # Aplicar factores del escenario
                self._aplicar_escenario(factores)
                
                # Optimizar modelo
                resultado = self.modelo.optimizar_objetivo_unico('costo')
                
                # Almacenar resultado
                resultados_escenarios[nombre_escenario] = {
                    'costo_total': resultado.costo_total,
                    'emisiones_co2': resultado.emisiones_co2,
                    'factor_social': resultado.factor_social,
                    'estado': resultado.estado_optimizacion,
                    'factores_aplicados': factores
                }
                
                # Restaurar parámetros originales
                self._restaurar_parametros_originales()
                
            except Exception as e:
                self.logger.error(f"Error en escenario {nombre_escenario}: {str(e)}")
                resultados_escenarios[nombre_escenario] = {
                    'error': str(e),
                    'factores_aplicados': factores
                }
                
        return resultados_escenarios
        
    def _aplicar_escenario(self, factores: Dict[str, float]) -> None:
        """Aplica factores de un escenario específico"""
        
        for parametro, factor in factores.items():
            if parametro == 'costos':
                for recurso in self.modelo.recursos.values():
                    recurso.costo_unitario *= factor
                    
            elif parametro == 'emisiones':
                for recurso in self.modelo.recursos.values():
                    recurso.factor_emision *= factor
                    
            elif parametro == 'demandas':
                for tarea in self.modelo.tareas.values():
                    tarea.demanda_anual *= factor
                    
            elif parametro == 'factores_sociales':
                for recurso in self.modelo.recursos.values():
                    recurso.factor_social = np.clip(recurso.factor_social * factor, 0, 1)
                    
    def exportar_resultados_incertidumbre(self, resultados: Dict[str, Any], archivo: str) -> None:
        """Exporta resultados de análisis de incertidumbre a Excel"""
        
        with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
            
            # Hoja 1: Resultados brutos
            if 'resultados_brutos' in resultados:
                df_brutos = pd.DataFrame(resultados['resultados_brutos'])
                df_brutos.to_excel(writer, sheet_name='Resultados_Brutos', index=False)
                
            # Hoja 2: Estadísticas
            if 'estadisticas' in resultados:
                estadisticas_flat = self._aplanar_diccionario(resultados['estadisticas'])
                df_estadisticas = pd.DataFrame.from_dict(estadisticas_flat, orient='index', columns=['Valor'])
                df_estadisticas.to_excel(writer, sheet_name='Estadisticas')
                
            # Hoja 3: Análisis
            if 'analisis' in resultados:
                analisis_flat = self._aplanar_diccionario(resultados['analisis'])
                df_analisis = pd.DataFrame.from_dict(analisis_flat, orient='index', columns=['Valor'])
                df_analisis.to_excel(writer, sheet_name='Analisis')
                
    def _aplanar_diccionario(self, d: Dict[str, Any], sep: str = '_') -> Dict[str, Any]:
        """Aplana un diccionario anidado"""
        
        resultado = {}
        
        for k, v in d.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    resultado[f"{k}{sep}{k2}"] = v2
            else:
                resultado[k] = v
                
        return resultado
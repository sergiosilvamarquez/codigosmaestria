"""
Base de datos de tecnologías energéticas con parámetros actualizables
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
import json
import os
from pathlib import Path
from .modelo_energetico import RecursoEnergetico, Tarea

class BaseDatosTecnologias:
    """
    Base de datos completa de tecnologías energéticas
    
    Incluye:
    - Parámetros técnico-económicos
    - Curvas de aprendizaje
    - Factores de escalamiento
    - Datos de literatura actualizada
    """
    
    def __init__(self, archivo_datos: Optional[str] = None):
        """
        Inicializa la base de datos
        
        Args:
            archivo_datos: Ruta a archivo Excel/JSON con datos personalizados
        """
        self.datos_tecnologias = {}
        self.curvas_aprendizaje = {}
        self.factores_regionales = {}
        
        # Cargar datos por defecto
        self._cargar_datos_por_defecto()
        
        # Cargar datos personalizados si se proporciona archivo
        if archivo_datos:
            self._cargar_datos_personalizados(archivo_datos)
            
    def _cargar_datos_por_defecto(self) -> None:
        """Carga datos técnico-económicos por defecto"""
        
        # Tecnologías renovables
        self.datos_tecnologias.update({
            'solar_fotovoltaico': {
                'factor_energia': 0.203,  # kWh/m²/día promedio
                'costo_capital': 1200,    # $/kW
                'costo_operacion': 0.02,  # $/kWh
                'factor_emision': 0.048,  # kgCO2/kWh (ciclo vida)
                'factor_social': 0.85,    # índice 0-1
                'vida_util': 25,
                'eficiencia_maxima': 0.22,
                'degradacion_anual': 0.005,
                'factor_capacidad': 0.25,
                'curva_aprendizaje': 0.24,  # reducción costo por duplicación
                'maduridad_tecnologica': 9,  # TRL 1-9
                'densidad_potencia': 150,   # W/m²
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.96,
                    'cargar_baterias': 0.95,
                    'cocinar': 0.90,
                    'motor_dc': 0.88
                }
            },
            
            'eolica_terrestre': {
                'factor_energia': 2.8,    # kWh/m²/día promedio
                'costo_capital': 1400,
                'costo_operacion': 0.015,
                'factor_emision': 0.011,
                'factor_social': 0.75,
                'vida_util': 20,
                'eficiencia_maxima': 0.45,
                'factor_capacidad': 0.35,
                'curva_aprendizaje': 0.15,
                'madureza_tecnologica': 9,
                'densidad_potencia': 2.5,   # W/m²
                'velocidad_arranque': 3.5,  # m/s
                'velocidad_nominal': 12,    # m/s
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.95,
                    'cargar_baterias': 0.93,
                    'cocinar': 0.88,
                    'motor_dc': 0.87
                }
            },
            
            'hidroelectrica_pequeña': {
                'factor_energia': 0.027,   # kWh/m³ (altura específica)
                'costo_capital': 2500,
                'costo_operacion': 0.01,
                'factor_emision': 0.024,
                'factor_social': 0.90,
                'vida_util': 50,
                'eficiencia_maxima': 0.90,
                'factor_capacidad': 0.50,
                'curva_aprendizaje': 0.05,
                'madureza_tecnologica': 9,
                'altura_minima': 3,        # metros
                'caudal_minimo': 0.1,      # m³/s
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.98,
                    'cargar_baterias': 0.96,
                    'cocinar': 0.92,
                    'motor_dc': 0.90
                }
            },
            
            'biogas': {
                'factor_energia': 5.55,    # kWh/m³
                'costo_capital': 3500,
                'costo_operacion': 0.03,
                'factor_emision': 0.2,     # neutro en carbono
                'factor_social': 0.95,     # alta aceptación rural
                'vida_util': 15,
                'eficiencia_maxima': 0.35,
                'factor_capacidad': 0.80,
                'curva_aprendizaje': 0.10,
                'madureza_tecnologica': 7,
                'temperatura_operacion': 35,  # °C óptima
                'tiempo_retencion': 20,       # días
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.85,
                    'cocinar': 0.95,
                    'cargar_baterias': 0.82,
                    'motor_dc': 0.80
                }
            }
        })
        
        # Tecnologías convencionales
        self.datos_tecnologias.update({
            'termica_carbon': {
                'factor_energia': 5.4,     # kWh/kg
                'costo_capital': 2800,
                'costo_operacion': 0.04,
                'factor_emision': 0.82,
                'factor_social': 0.30,
                'vida_util': 30,
                'eficiencia_maxima': 0.45,
                'factor_capacidad': 0.85,
                'curva_aprendizaje': 0.02,
                'madureza_tecnologica': 9,
                'rampa_maxima': 30,        # %/hora
                'tiempo_arranque': 8,      # horas
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.95,
                    'cargar_baterias': 0.93,
                    'cocinar': 0.88,
                    'motor_dc': 0.85
                }
            },
            
            'termica_gas_natural': {
                'factor_energia': 11.5,    # kWh/m³
                'costo_capital': 1000,
                'costo_operacion': 0.055,
                'factor_emision': 0.35,
                'factor_social': 0.50,
                'vida_util': 25,
                'eficiencia_maxima': 0.60,
                'factor_capacidad': 0.90,
                'curva_aprendizaje': 0.03,
                'madureza_tecnologica': 9,
                'rampa_maxima': 60,        # %/hora
                'tiempo_arranque': 1,      # horas
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.96,
                    'cocinar': 0.98,
                    'cargar_baterias': 0.94,
                    'motor_dc': 0.90
                }
            },
            
            'termica_combustoleo': {
                'factor_energia': 1777,    # kWh/barril
                'costo_capital': 1200,
                'costo_operacion': 0.08,
                'factor_emision': 0.75,
                'factor_social': 0.25,
                'vida_util': 20,
                'eficiencia_maxima': 0.42,
                'factor_capacidad': 0.75,
                'curva_aprendizaje': 0.01,
                'madureza_tecnologica': 9,
                'rampa_maxima': 50,        # %/hora
                'tiempo_arranque': 4,      # horas
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.94,
                    'cargar_baterias': 0.92,
                    'cocinar': 0.85,
                    'motor_dc': 0.82
                }
            }
        })
        
        # Sistemas de almacenamiento
        self.datos_tecnologias.update({
            'bateria_ion_litio': {
                'factor_energia': 1.0,     # kWh/kWh
                'costo_capital': 300,      # $/kWh
                'costo_operacion': 0.01,
                'factor_emision': 0.06,
                'factor_social': 0.70,
                'vida_util': 15,
                'eficiencia_maxima': 0.95,
                'factor_capacidad': 1.0,
                'curva_aprendizaje': 0.18,
                'madureza_tecnologica': 8,
                'profundidad_descarga': 0.90,
                'autodescarga': 0.0005,     # por día
                'ciclos_vida': 6000,
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.95,
                    'cargar_baterias': 1.0,
                    'cocinar': 0.92,
                    'motor_dc': 0.95
                }
            },
            
            'bateria_plomo_acido': {
                'factor_energia': 1.0,
                'costo_capital': 150,      # $/kWh
                'costo_operacion': 0.02,
                'factor_emision': 0.10,
                'factor_social': 0.60,
                'vida_util': 8,
                'eficiencia_maxima': 0.85,
                'factor_capacidad': 1.0,
                'curva_aprendizaje': 0.05,
                'madureza_tecnologica': 9,
                'profundidad_descarga': 0.50,
                'autodescarga': 0.003,      # por día
                'ciclos_vida': 1500,
                'eficiencias_por_tarea': {
                    'electricidad_ac': 0.85,
                    'cargar_baterias': 1.0,
                    'cocinar': 0.80,
                    'motor_dc': 0.85
                }
            }
        })
        
        # Cargar curvas de aprendizaje
        self._cargar_curvas_aprendizaje()
        
        # Cargar factores regionales
        self._cargar_factores_regionales()
        
    def _cargar_curvas_aprendizaje(self) -> None:
        """Carga modelos de curvas de aprendizaje por tecnología"""
        
        # Curva típica: Costo(t) = Costo_inicial * (Capacidad_acumulada(t) / Capacidad_inicial)^(-learning_rate)
        self.curvas_aprendizaje = {
            'solar_fotovoltaico': {
                'learning_rate': 0.24,     # 24% reducción por duplicación
                'año_base': 2020,
                'costo_base': 1200,
                'capacidad_base': 700,     # GW mundial
                'crecimiento_anual': 0.25,
                'costo_minimo': 400,       # límite teórico
            },
            'eolica_terrestre': {
                'learning_rate': 0.15,
                'año_base': 2020,
                'costo_base': 1400,
                'capacidad_base': 730,     # GW mundial
                'crecimiento_anual': 0.15,
                'costo_minimo': 800,
            },
            'bateria_ion_litio': {
                'learning_rate': 0.18,
                'año_base': 2020,
                'costo_base': 300,
                'capacidad_base': 500,     # GWh mundial
                'crecimiento_anual': 0.30,
                'costo_minimo': 50,
            }
        }
        
    def _cargar_factores_regionales(self) -> None:
        """Carga factores de ajuste regional"""
        
        self.factores_regionales = {
            'mexico': {
                'factor_costo': 0.85,      # costos 15% menores
                'factor_social': 1.10,     # mayor impacto social
                'irradiacion_solar': 2100, # kWh/m²/año promedio
                'velocidad_viento': 6.5,   # m/s promedio
                'disponibilidad_biomasa': 0.80,
                'factor_mano_obra': 0.60,
            },
            'colombia': {
                'factor_costo': 0.90,
                'factor_social': 1.05,
                'irradiacion_solar': 1800,
                'velocidad_viento': 5.8,
                'disponibilidad_biomasa': 0.85,
                'factor_mano_obra': 0.65,
            },
            'chile': {
                'factor_costo': 1.10,
                'factor_social': 0.95,
                'irradiacion_solar': 2500,
                'velocidad_viento': 8.2,
                'disponibilidad_biomasa': 0.40,
                'factor_mano_obra': 0.85,
            }
        }
        
    def obtener_recurso_energetico(self, tecnologia: str, capacidad: float,
                                 region: str = 'mexico', año: int = 2024) -> RecursoEnergetico:
        """
        Crea un RecursoEnergetico con parámetros actualizados
        
        Args:
            tecnologia: Nombre de la tecnología
            capacidad: Capacidad máxima (kWh/año)
            region: Región geográfica
            año: Año de referencia para costos
            
        Returns:
            RecursoEnergetico configurado
        """
        if tecnologia not in self.datos_tecnologias:
            raise ValueError(f"Tecnología '{tecnologia}' no encontrada")
            
        datos = self.datos_tecnologias[tecnologia].copy()
        
        # Aplicar curva de aprendizaje
        if tecnologia in self.curvas_aprendizaje:
            datos['costo_capital'] = self._calcular_costo_con_aprendizaje(tecnologia, año)
            
        # Aplicar factores regionales
        if region in self.factores_regionales:
            factor_regional = self.factores_regionales[region]
            datos['costo_capital'] *= factor_regional['factor_costo']
            datos['costo_operacion'] *= factor_regional['factor_costo']
            datos['factor_social'] *= factor_regional['factor_social']
            
            # Ajustar factor de energía según recurso regional
            if 'solar' in tecnologia:
                datos['factor_energia'] *= factor_regional['irradiacion_solar'] / 2000  # normalizado
            elif 'eolica' in tecnologia:
                datos['factor_energia'] *= (factor_regional['velocidad_viento'] / 7.0)**3
            elif 'biogas' in tecnologia:
                datos['factor_energia'] *= factor_regional['disponibilidad_biomasa']
                
        return RecursoEnergetico(
            nombre=tecnologia,
            capacidad_maxima=capacidad,
            factor_energia=datos['factor_energia'],
            costo_unitario=datos['costo_operacion'],
            factor_emision=datos['factor_emision'],
            factor_social=datos['factor_social'],
            vida_util=datos['vida_util'],
            costo_mantenimiento=datos.get('costo_mantenimiento', 0.02),
            eficiencia=datos['eficiencias_por_tarea'],
            rampa_maxima=datos.get('rampa_maxima'),
            almacenable=(tecnologia.startswith('bateria'))
        )
        
    def _calcular_costo_con_aprendizaje(self, tecnologia: str, año: int) -> float:
        """Calcula costo con curva de aprendizaje"""
        curva = self.curvas_aprendizaje[tecnologia]
        
        años_transcurridos = año - curva['año_base']
        if años_transcurridos <= 0:
            return curva['costo_base']
            
        # Calcular capacidad acumulada
        capacidad_actual = curva['capacidad_base'] * (1 + curva['crecimiento_anual'])**años_transcurridos
        ratio_capacidad = capacidad_actual / curva['capacidad_base']
        
        # Aplicar curva de aprendizaje
        costo_actual = curva['costo_base'] * (ratio_capacidad**(-curva['learning_rate']))
        
        # Aplicar límite mínimo
        return max(costo_actual, curva['costo_minimo'])
        
    def crear_tareas_tipicas(self, escala: str = 'residencial') -> Dict[str, Tarea]:
        """
        Crea conjunto típico de tareas según escala
        
        Args:
            escala: 'residencial', 'comercial', 'industrial'
            
        Returns:
            Diccionario de tareas configuradas
        """
        if escala == 'residencial':
            return {
                'electricidad_ac': Tarea(
                    nombre='electricidad_ac',
                    demanda_anual=3650,      # kWh/año (10 kWh/día)
                    potencia_maxima=5,       # kW
                    perfil_temporal=self._generar_perfil_residencial(),
                    prioridad=1
                ),
                'cocinar': Tarea(
                    nombre='cocinar',
                    demanda_anual=1095,      # kWh/año (3 kWh/día)
                    potencia_maxima=3,       # kW
                    perfil_temporal=self._generar_perfil_cocina(),
                    prioridad=1
                ),
                'cargar_baterias': Tarea(
                    nombre='cargar_baterias',
                    demanda_anual=730,       # kWh/año (2 kWh/día)
                    potencia_maxima=2,       # kW
                    prioridad=2
                ),
                'motor_dc': Tarea(
                    nombre='motor_dc',
                    demanda_anual=1460,      # kWh/año (4 kWh/día)
                    potencia_maxima=1.5,     # kW
                    prioridad=3
                )
            }
        elif escala == 'comercial':
            return {
                'electricidad_ac': Tarea(
                    nombre='electricidad_ac',
                    demanda_anual=50000,     # kWh/año
                    potencia_maxima=25,      # kW
                    perfil_temporal=self._generar_perfil_comercial(),
                    prioridad=1
                ),
                'climatizacion': Tarea(
                    nombre='climatizacion',
                    demanda_anual=30000,     # kWh/año
                    potencia_maxima=15,      # kW
                    prioridad=2
                ),
                'cargar_baterias': Tarea(
                    nombre='cargar_baterias',
                    demanda_anual=5000,      # kWh/año
                    potencia_maxima=10,      # kW
                    prioridad=2
                )
            }
        elif escala == 'industrial':
            return {
                'electricidad_ac': Tarea(
                    nombre='electricidad_ac',
                    demanda_anual=500000,    # kWh/año
                    potencia_maxima=200,     # kW
                    perfil_temporal=self._generar_perfil_industrial(),
                    prioridad=1
                ),
                'procesos_industriales': Tarea(
                    nombre='procesos_industriales',
                    demanda_anual=800000,    # kWh/año
                    potencia_maxima=350,     # kW
                    prioridad=1
                ),
                'cargar_baterias': Tarea(
                    nombre='cargar_baterias',
                    demanda_anual=50000,     # kWh/año
                    potencia_maxima=100,     # kW
                    prioridad=3
                )
            }
        else:
            raise ValueError(f"Escala '{escala}' no reconocida")
            
    def _generar_perfil_residencial(self) -> np.ndarray:
        """Genera perfil típico de demanda residencial (24 horas)"""
        perfil = np.array([
            0.4, 0.3, 0.3, 0.3, 0.3, 0.4,  # 00-05: bajo consumo nocturno
            0.5, 0.7, 0.8, 0.6, 0.5, 0.6,  # 06-11: mañana
            0.7, 0.6, 0.5, 0.5, 0.6, 0.7,  # 12-17: tarde
            0.9, 1.0, 0.9, 0.8, 0.7, 0.5   # 18-23: pico vespertino
        ])
        return perfil / perfil.sum()  # normalizar
        
    def _generar_perfil_cocina(self) -> np.ndarray:
        """Genera perfil típico de cocina (24 horas)"""
        perfil = np.array([
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0,  # 00-05: sin uso
            0.1, 0.3, 0.2, 0.1, 0.1, 0.1,  # 06-11: desayuno
            0.2, 0.3, 0.4, 0.2, 0.1, 0.1,  # 12-17: comida
            0.2, 0.4, 0.6, 0.3, 0.1, 0.0   # 18-23: cena
        ])
        return perfil / perfil.sum()
        
    def _generar_perfil_comercial(self) -> np.ndarray:
        """Genera perfil típico comercial (24 horas)"""
        perfil = np.array([
            0.2, 0.2, 0.2, 0.2, 0.2, 0.3,  # 00-05: seguridad básica
            0.4, 0.6, 0.8, 0.9, 0.9, 0.9,  # 06-11: apertura
            0.9, 0.9, 0.9, 0.9, 0.9, 0.9,  # 12-17: operación plena
            0.8, 0.7, 0.6, 0.4, 0.3, 0.2   # 18-23: cierre
        ])
        return perfil / perfil.sum()
        
    def _generar_perfil_industrial(self) -> np.ndarray:
        """Genera perfil típico industrial (24 horas)"""
        # Operación continua con mantenimiento en madrugada
        perfil = np.array([
            0.7, 0.6, 0.5, 0.5, 0.6, 0.7,  # 00-05: turno nocturno reducido
            0.8, 0.9, 1.0, 1.0, 1.0, 1.0,  # 06-11: primer turno
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0,  # 12-17: segundo turno
            0.9, 0.9, 0.8, 0.8, 0.7, 0.7   # 18-23: tercer turno
        ])
        return perfil / perfil.sum()
        
    def exportar_base_datos(self, archivo: str) -> None:
        """Exporta la base de datos completa a Excel"""
        with pd.ExcelWriter(archivo, engine='openpyxl') as writer:
            # Hoja 1: Tecnologías
            df_tecnologias = pd.DataFrame.from_dict(self.datos_tecnologias, orient='index')
            df_tecnologias.to_excel(writer, sheet_name='Tecnologias')
            
            # Hoja 2: Curvas de aprendizaje
            df_curvas = pd.DataFrame.from_dict(self.curvas_aprendizaje, orient='index')
            df_curvas.to_excel(writer, sheet_name='Curvas_Aprendizaje')
            
            # Hoja 3: Factores regionales
            df_regiones = pd.DataFrame.from_dict(self.factores_regionales, orient='index')
            df_regiones.to_excel(writer, sheet_name='Factores_Regionales')
            
    def importar_base_datos(self, archivo: str) -> None:
        """Importa base de datos desde Excel"""
        try:
            # Leer tecnologías
            df_tecnologias = pd.read_excel(archivo, sheet_name='Tecnologias', index_col=0)
            self.datos_tecnologias = df_tecnologias.to_dict('index')
            
            # Leer curvas de aprendizaje
            df_curvas = pd.read_excel(archivo, sheet_name='Curvas_Aprendizaje', index_col=0)
            self.curvas_aprendizaje = df_curvas.to_dict('index')
            
            # Leer factores regionales
            df_regiones = pd.read_excel(archivo, sheet_name='Factores_Regionales', index_col=0)
            self.factores_regionales = df_regiones.to_dict('index')
            
        except Exception as e:
            print(f"Error al importar base de datos: {e}")
            
    def obtener_tecnologias_disponibles(self) -> List[str]:
        """Retorna lista de tecnologías disponibles"""
        return list(self.datos_tecnologias.keys())
        
    def obtener_regiones_disponibles(self) -> List[str]:
        """Retorna lista de regiones disponibles"""
        return list(self.factores_regionales.keys())
        
    def comparar_tecnologias(self, criterio: str = 'costo_capital') -> pd.DataFrame:
        """
        Compara tecnologías según criterio específico
        
        Args:
            criterio: 'costo_capital', 'factor_emision', 'factor_social', etc.
            
        Returns:
            DataFrame ordenado por criterio
        """
        datos = []
        for tech, params in self.datos_tecnologias.items():
            if criterio in params:
                datos.append({
                    'tecnologia': tech,
                    'valor': params[criterio],
                    'vida_util': params.get('vida_util', 0),
                    'factor_social': params.get('factor_social', 0),
                    'factor_emision': params.get('factor_emision', 0)
                })
                
        df = pd.DataFrame(datos)
        return df.sort_values('valor')
        
    def actualizar_tecnologia(self, nombre: str, parametros: Dict[str, Any]) -> None:
        """
        Actualiza parámetros de una tecnología existente
        
        Args:
            nombre: Nombre de la tecnología
            parametros: Diccionario con parámetros a actualizar
        """
        if nombre not in self.datos_tecnologias:
            raise ValueError(f"Tecnología '{nombre}' no encontrada")
            
        self.datos_tecnologias[nombre].update(parametros)
        
    def agregar_tecnologia_personalizada(self, nombre: str, parametros: Dict[str, Any]) -> None:
        """
        Agrega una nueva tecnología personalizada
        
        Args:
            nombre: Nombre de la nueva tecnología
            parametros: Diccionario completo de parámetros
        """
        # Validar parámetros mínimos requeridos
        requeridos = ['factor_energia', 'costo_capital', 'costo_operacion', 
                     'factor_emision', 'factor_social', 'vida_util']
        
        for param in requeridos:
            if param not in parametros:
                raise ValueError(f"Parámetro requerido '{param}' no encontrado")
                
        self.datos_tecnologias[nombre] = parametros
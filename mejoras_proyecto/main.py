#!/usr/bin/env python3
"""
Sistema de Optimización Energética Sustentable - Versión Mejorada
Archivo principal de demostración

Autor: Ing. Sergio Isaías Silva Márquez
Versión: 2.0.0
"""

import sys
import logging
import argparse
from pathlib import Path
import time

# Configurar el path para importar módulos locales
sys.path.insert(0, str(Path(__file__).parent))

from src.modelos.modelo_energetico import ModeloEnergetico
from src.modelos.tecnologias import BaseDatosTecnologias
from src.modelos.validacion import ValidadorParametros
from src.optimizacion.optimizador_principal import OptimizadorEnergetico

def configurar_logging(nivel=logging.INFO):
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=nivel,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('optimizacion_energetica.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

def crear_ejemplo_residencial():
    """Crea un ejemplo de sistema energético residencial"""
    
    print("🏠 Creando ejemplo de sistema energético residencial...")
    
    # Inicializar base de datos de tecnologías
    base_datos = BaseDatosTecnologias()
    
    # Crear modelo energético
    modelo = ModeloEnergetico(horizonte_temporal=24)  # Modelado diario
    
    # Agregar recursos energéticos
    print("   ⚡ Agregando recursos energéticos...")
    
    # Solar fotovoltaico
    recurso_solar = base_datos.obtener_recurso_energetico(
        'solar_fotovoltaico', 
        capacidad=50000,  # kWh/año (suficiente para casa residencial)
        region='mexico'
    )
    modelo.agregar_recurso(recurso_solar)
    
    # Biogas
    recurso_biogas = base_datos.obtener_recurso_energetico(
        'biogas',
        capacidad=20000,  # kWh/año 
        region='mexico'
    )
    modelo.agregar_recurso(recurso_biogas)
    
    # Gas natural (respaldo)
    recurso_gas = base_datos.obtener_recurso_energetico(
        'termica_gas_natural',
        capacidad=30000,  # kWh/año
        region='mexico'
    )
    modelo.agregar_recurso(recurso_gas)
    
    # Agregar tareas/demandas
    print("   🏡 Agregando demandas energéticas...")
    
    tareas = base_datos.crear_tareas_tipicas('residencial')
    for tarea in tareas.values():
        modelo.agregar_tarea(tarea)
    
    # Configurar almacenamiento
    print("   🔋 Configurando sistema de almacenamiento...")
    modelo.configurar_almacenamiento(
        capacidad=20,      # kWh
        eficiencia=0.95,   # 95%
        autodescarga=0.001 # 0.1% por hora
    )
    
    return modelo

def crear_ejemplo_industrial():
    """Crea un ejemplo de sistema energético industrial"""
    
    print("🏭 Creando ejemplo de sistema energético industrial...")
    
    base_datos = BaseDatosTecnologias()
    modelo = ModeloEnergetico(horizonte_temporal=8760)  # Modelado anual
    
    # Recursos más grandes para industria
    print("   ⚡ Agregando recursos industriales...")
    
    # Mix energético industrial
    recursos_config = [
        ('solar_fotovoltaico', 2000000),    # 2 GWh/año
        ('eolica_terrestre', 3000000),      # 3 GWh/año
        ('termica_gas_natural', 5000000),   # 5 GWh/año
        ('hidroelectrica_pequeña', 1000000), # 1 GWh/año
    ]
    
    for tech, capacidad in recursos_config:
        recurso = base_datos.obtener_recurso_energetico(tech, capacidad, 'mexico')
        modelo.agregar_recurso(recurso)
    
    # Tareas industriales
    print("   🏭 Agregando demandas industriales...")
    tareas = base_datos.crear_tareas_tipicas('industrial')
    for tarea in tareas.values():
        modelo.agregar_tarea(tarea)
    
    # Almacenamiento industrial
    modelo.configurar_almacenamiento(capacidad=500, eficiencia=0.90)
    
    return modelo

def ejecutar_optimizacion_completa(modelo, nombre_caso):
    """Ejecuta optimización completa y muestra resultados"""
    
    print(f"\n🚀 Iniciando optimización completa para caso: {nombre_caso}")
    print("=" * 60)
    
    # Crear optimizador
    optimizador = OptimizadorEnergetico(modelo, validar_modelo=True)
    
    # 1. Validación del modelo
    print("\n1️⃣ Validación del modelo...")
    es_valido, errores = optimizador.validador.validar_completo()
    
    if es_valido:
        print("   ✅ Modelo válido!")
    else:
        print(f"   ⚠️  Modelo con {len(errores)} problemas")
        print("   📋 Generando reporte de validación...")
        reporte = optimizador.validador.generar_reporte_validacion()
        print(reporte[:500] + "..." if len(reporte) > 500 else reporte)
    
    # 2. Optimización de objetivos únicos
    print("\n2️⃣ Optimización de objetivos únicos...")
    
    objetivos = ['costo', 'co2', 'social']
    resultados_individuales = {}
    
    for objetivo in objetivos:
        print(f"   📊 Optimizando {objetivo}...")
        start_time = time.time()
        
        resultado = optimizador.optimizar_objetivo_unico(objetivo)
        resultados_individuales[objetivo] = resultado
        
        print(f"      ⏱️  Tiempo: {time.time() - start_time:.2f}s")
        print(f"      💰 Costo: ${resultado.costo_total:,.0f}")
        print(f"      🌱 CO2: {resultado.emisiones_co2:,.0f} kg")
        print(f"      👥 Social: {resultado.factor_social:.2f}")
        print(f"      📈 Estado: {resultado.estado_optimizacion}")
    
    # 3. Optimización multiobjetivo
    print("\n3️⃣ Optimización multiobjetivo...")
    
    # Método por ponderación
    print("   ⚖️  Método por ponderación...")
    resultado_ponderacion = optimizador.optimizar_multiobjetivo('ponderacion')
    
    if 'error' not in resultado_ponderacion:
        n_soluciones = len(resultado_ponderacion['resultados'])
        print(f"      ✅ {n_soluciones} soluciones encontradas")
        
        mejor = resultado_ponderacion['mejor_solucion']
        if mejor:
            print(f"      🏆 Mejor solución: ${mejor.costo_total:,.0f}, {mejor.emisiones_co2:,.0f} kg CO2")
    
    # Generar frente Pareto
    print("   📈 Generando frente Pareto...")
    frente_pareto = optimizador.generar_frente_pareto_completo(['ponderacion'], n_puntos=20)
    
    if len(frente_pareto) > 0:
        print(f"      ✅ Frente Pareto con {len(frente_pareto)} puntos")
        print(f"      💰 Rango costos: ${frente_pareto[:, 0].min():,.0f} - ${frente_pareto[:, 0].max():,.0f}")
        print(f"      🌱 Rango CO2: {frente_pareto[:, 1].min():,.0f} - {frente_pareto[:, 1].max():,.0f} kg")
        print(f"      👥 Rango social: {frente_pareto[:, 2].min():.2f} - {frente_pareto[:, 2].max():.2f}")
    
    # 4. Análisis de sensibilidad
    print("\n4️⃣ Análisis de sensibilidad...")
    
    try:
        sensibilidad = optimizador.analisis_sensibilidad_completo(
            parametros=['costos'],
            variacion=0.1,
            n_puntos=5
        )
        
        if sensibilidad:
            print("   ✅ Análisis de sensibilidad completado")
            for param, df in sensibilidad.items():
                print(f"      📊 {param}: {len(df)} puntos analizados")
        
    except Exception as e:
        print(f"   ⚠️  Error en análisis de sensibilidad: {str(e)}")
    
    # 5. Exportar resultados
    print("\n5️⃣ Exportando resultados...")
    
    try:
        archivo_base = f"results/{nombre_caso}"
        optimizador.exportar_resultados_completos(archivo_base)
        print(f"   ✅ Resultados exportados a {archivo_base}_*.xlsx")
        
    except Exception as e:
        print(f"   ⚠️  Error en exportación: {str(e)}")
    
    # 6. Resumen final
    print("\n6️⃣ Resumen de optimización...")
    resumen = optimizador.obtener_resumen_optimizacion()
    
    print(f"   📊 Total optimizaciones: {resumen['total_optimizaciones']}")
    print(f"   🔬 Métodos utilizados: {', '.join(resumen['metodos_utilizados'])}")
    print(f"   📈 Puntos Pareto: {resumen['frente_pareto_puntos']}")
    print(f"   ⏱️  Tiempo total: {resumen['tiempo_total_optimizacion']:.2f}s")
    
    return optimizador, resultados_individuales

def ejecutar_comparacion_tecnologias():
    """Ejecuta comparación de tecnologías"""
    
    print("\n🔬 Análisis comparativo de tecnologías")
    print("=" * 60)
    
    base_datos = BaseDatosTecnologias()
    
    # Comparar por diferentes criterios
    criterios = ['costo_capital', 'factor_emision', 'factor_social']
    
    for criterio in criterios:
        print(f"\n📊 Comparación por {criterio}:")
        
        try:
            df_comparacion = base_datos.comparar_tecnologias(criterio)
            
            print(f"   🏆 Top 3 mejores tecnologías:")
            for i, (_, row) in enumerate(df_comparacion.head(3).iterrows()):
                print(f"   {i+1}. {row['tecnologia']}: {row['valor']:.3f}")
                
        except Exception as e:
            print(f"   ⚠️  Error: {str(e)}")

def mostrar_ayuda():
    """Muestra información de ayuda"""
    
    print("""
🌟 Sistema de Optimización Energética Sustentable - v2.0
========================================================

CARACTERÍSTICAS PRINCIPALES:
✅ Optimización multiobjetivo (costo, CO2, social)
✅ Múltiples algoritmos (CVXPY, SciPy, PuLP)
✅ Base de datos de tecnologías actualizable
✅ Validación exhaustiva de parámetros
✅ Análisis de sensibilidad e incertidumbre
✅ Modelado temporal con almacenamiento
✅ Interfaz moderna y reportes automáticos

MODOS DE EJECUCIÓN:
python main.py --modo residencial    # Ejemplo residencial
python main.py --modo industrial     # Ejemplo industrial  
python main.py --modo comparacion    # Comparar tecnologías
python main.py --modo gui           # Interfaz gráfica (próximamente)

MEJORAS RESPECTO A LA VERSIÓN ORIGINAL:
🚀 Sin dependencia de GAMS - 100% Python
🔧 Validación robusta con corrección automática
📊 Análisis de incertidumbre Monte Carlo
⚡ Paralelización automática
🎯 Múltiples métodos multiobjetivo
📈 Visualizaciones interactivas
💾 Base de datos de tecnologías expandible
🔬 Casos de prueba automatizados

DOCUMENTACIÓN COMPLETA:
📖 Ver README.md para instalación detallada
📋 Ver docs/ para documentación técnica
🧪 Ver examples/ para más casos de uso
    """)

def main():
    """Función principal"""
    
    # Configurar argumentos de línea de comandos
    parser = argparse.ArgumentParser(
        description='Sistema de Optimización Energética Sustentable v2.0'
    )
    parser.add_argument(
        '--modo', 
        choices=['residencial', 'industrial', 'comparacion', 'gui', 'ayuda'],
        default='ayuda',
        help='Modo de ejecución del sistema'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    parser.add_argument(
        '--exportar',
        default='resultados',
        help='Directorio base para exportar resultados'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    nivel = logging.DEBUG if args.verbose else logging.INFO
    configurar_logging(nivel)
    
    # Crear directorio de resultados
    Path(args.exportar).mkdir(exist_ok=True)
    
    # Mensaje de bienvenida
    print("🌟" * 30)
    print("🌟  SISTEMA DE OPTIMIZACIÓN ENERGÉTICA SUSTENTABLE v2.0  🌟")
    print("🌟  Sin GAMS - 100% Python - Algoritmos Avanzados      🌟")
    print("🌟" * 30)
    print(f"🚀 Modo seleccionado: {args.modo.upper()}")
    print(f"📁 Directorio de resultados: {args.exportar}")
    
    # Ejecutar según modo seleccionado
    try:
        inicio_total = time.time()
        
        if args.modo == 'ayuda':
            mostrar_ayuda()
            
        elif args.modo == 'residencial':
            modelo = crear_ejemplo_residencial()
            optimizador, resultados = ejecutar_optimizacion_completa(modelo, 'residencial')
            
        elif args.modo == 'industrial':
            modelo = crear_ejemplo_industrial()
            optimizador, resultados = ejecutar_optimizacion_completa(modelo, 'industrial')
            
        elif args.modo == 'comparacion':
            ejecutar_comparacion_tecnologias()
            
        elif args.modo == 'gui':
            print("🎨 Interfaz gráfica en desarrollo...")
            print("💡 Por ahora, usa los modos de línea de comandos")
            mostrar_ayuda()
            
        tiempo_total = time.time() - inicio_total
        
        print(f"\n⏱️  Tiempo total de ejecución: {tiempo_total:.2f} segundos")
        print("\n✅ ¡Ejecución completada exitosamente!")
        print("\n📊 Revisa los archivos generados en el directorio de resultados")
        print("📋 Consulta el archivo de log para detalles técnicos")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Ejecución interrumpida por el usuario")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error durante la ejecución: {str(e)}")
        logging.exception("Error no controlado en main()")
        sys.exit(1)

if __name__ == "__main__":
    main()
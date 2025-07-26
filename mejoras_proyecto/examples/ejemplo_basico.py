#!/usr/bin/env python3
"""
Ejemplo básico de uso del Sistema de Optimización Energética v2.0
"""

import sys
from pathlib import Path

# Agregar directorio padre al path
sys.path.append(str(Path(__file__).parent.parent))

from src.modelos.modelo_energetico import ModeloEnergetico, RecursoEnergetico, Tarea
from src.modelos.tecnologias import BaseDatosTecnologias
from src.optimizacion.optimizador_principal import OptimizadorEnergetico

def ejemplo_basico():
    """Ejemplo básico de uso del sistema"""
    
    print("🌟 Ejemplo Básico - Sistema de Optimización Energética v2.0")
    print("=" * 60)
    
    # 1. Crear modelo energético
    print("\n1️⃣ Creando modelo energético...")
    modelo = ModeloEnergetico(horizonte_temporal=24)  # Día completo
    
    # 2. Usar base de datos de tecnologías
    print("2️⃣ Cargando base de datos de tecnologías...")
    base_datos = BaseDatosTecnologias()
    
    # 3. Agregar recursos energéticos
    print("3️⃣ Agregando recursos energéticos...")
    
    # Solar fotovoltaico
    solar = base_datos.obtener_recurso_energetico(
        'solar_fotovoltaico', 
        capacidad=10000,  # kWh/año
        region='mexico'
    )
    modelo.agregar_recurso(solar)
    print(f"   ✅ Agregado: {solar.nombre}")
    
    # Gas natural
    gas = base_datos.obtener_recurso_energetico(
        'termica_gas_natural',
        capacidad=15000,  # kWh/año
        region='mexico'
    )
    modelo.agregar_recurso(gas)
    print(f"   ✅ Agregado: {gas.nombre}")
    
    # 4. Agregar tareas/demandas
    print("4️⃣ Agregando demandas energéticas...")
    
    tareas = base_datos.crear_tareas_tipicas('residencial')
    for nombre, tarea in tareas.items():
        modelo.agregar_tarea(tarea)
        print(f"   ✅ Agregada tarea: {nombre} ({tarea.demanda_anual:,.0f} kWh/año)")
    
    # 5. Configurar almacenamiento
    print("5️⃣ Configurando almacenamiento...")
    modelo.configurar_almacenamiento(
        capacidad=10,      # kWh
        eficiencia=0.95,   # 95%
        autodescarga=0.001 # 0.1% por hora
    )
    print("   ✅ Almacenamiento configurado")
    
    # 6. Crear optimizador
    print("6️⃣ Creando optimizador...")
    optimizador = OptimizadorEnergetico(modelo, validar_modelo=True)
    print("   ✅ Optimizador creado y modelo validado")
    
    # 7. Optimizar objetivos individuales
    print("\n7️⃣ Optimizando objetivos individuales...")
    
    objetivos = ['costo', 'co2', 'social']
    resultados = {}
    
    for objetivo in objetivos:
        print(f"\n   📊 Optimizando {objetivo.upper()}...")
        resultado = optimizador.optimizar_objetivo_unico(objetivo)
        resultados[objetivo] = resultado
        
        print(f"      💰 Costo total: ${resultado.costo_total:,.0f}")
        print(f"      🌱 Emisiones CO2: {resultado.emisiones_co2:,.0f} kg")
        print(f"      👥 Factor social: {resultado.factor_social:.2f}")
        print(f"      📈 Estado: {resultado.estado_optimizacion}")
        print(f"      ⏱️  Tiempo: {resultado.tiempo_solucion:.2f}s")
    
    # 8. Optimización multiobjetivo
    print("\n8️⃣ Optimización multiobjetivo...")
    
    print("   ⚖️  Método por ponderación...")
    resultado_multi = optimizador.optimizar_multiobjetivo('ponderacion')
    
    if 'error' not in resultado_multi:
        print(f"   ✅ {len(resultado_multi['resultados'])} soluciones encontradas")
        
        mejor = resultado_multi['mejor_solucion']
        if mejor:
            print(f"   🏆 Mejor solución combinada:")
            print(f"      💰 Costo: ${mejor.costo_total:,.0f}")
            print(f"      🌱 CO2: {mejor.emisiones_co2:,.0f} kg")
            print(f"      👥 Social: {mejor.factor_social:.2f}")
    else:
        print(f"   ❌ Error: {resultado_multi['error']}")
    
    # 9. Análisis de sensibilidad
    print("\n9️⃣ Análisis de sensibilidad...")
    
    try:
        sensibilidad = optimizador.analisis_sensibilidad_completo(
            parametros=['costos'],
            variacion=0.1,
            n_puntos=5
        )
        
        if sensibilidad:
            print("   ✅ Análisis completado")
            for param, df in sensibilidad.items():
                variacion_max = df['costo'].max() - df['costo'].min()
                print(f"   📊 {param}: variación máxima de ${variacion_max:,.0f}")
        
    except Exception as e:
        print(f"   ⚠️  Error en sensibilidad: {str(e)}")
    
    # 10. Comparación de tecnologías
    print("\n🔟 Comparación de tecnologías...")
    
    print("   📊 Ranking por costo de capital:")
    comparacion = base_datos.comparar_tecnologias('costo_capital')
    for i, (_, row) in enumerate(comparacion.head(3).iterrows()):
        print(f"   {i+1}. {row['tecnologia']}: ${row['valor']:,.0f}/kW")
    
    # 11. Resumen final
    print("\n📋 RESUMEN FINAL")
    print("=" * 40)
    
    resumen = optimizador.obtener_resumen_optimizacion()
    print(f"✅ Optimizaciones realizadas: {resumen['total_optimizaciones']}")
    print(f"🔬 Métodos utilizados: {', '.join(resumen['metodos_utilizados'])}")
    print(f"⏱️  Tiempo total: {resumen['tiempo_total_optimizacion']:.2f}s")
    
    # Mostrar mejor solución por criterio
    if resultados:
        mejor_costo = min(resultados.values(), key=lambda x: x.costo_total)
        menor_co2 = min(resultados.values(), key=lambda x: x.emisiones_co2)
        mayor_social = max(resultados.values(), key=lambda x: x.factor_social)
        
        print(f"\n🏆 MEJORES SOLUCIONES:")
        print(f"💰 Menor costo: ${mejor_costo.costo_total:,.0f}")
        print(f"🌱 Menores emisiones: {menor_co2.emisiones_co2:,.0f} kg CO2")
        print(f"👥 Mayor factor social: {mayor_social.factor_social:.2f}")
    
    print("\n✅ ¡Ejemplo completado exitosamente!")
    print("📖 Ver documentación para casos más avanzados")
    
    return optimizador, resultados

if __name__ == "__main__":
    optimizador, resultados = ejemplo_basico()
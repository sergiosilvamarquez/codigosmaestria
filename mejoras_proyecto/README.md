# Sistema de Optimización Energética Sustentable - Versión Mejorada

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 Descripción

Sistema avanzado de optimización multiobjetivo para el diseño sustentable de centrales eléctricas. Esta versión mejorada incluye múltiples algoritmos de optimización, análisis de incertidumbre, y una interfaz gráfica moderna.

### ✨ Características Principales

- **🔧 Múltiples Algoritmos**: Soporte para algoritmos genéticos, PSO, programación lineal
- **📊 Análisis Multiobjetivo**: Optimización simultánea de costos, emisiones CO2 y factores sociales
- **🔄 Análisis de Incertidumbre**: Simulaciones Monte Carlo y análisis de sensibilidad
- **⚡ Modelado Temporal**: Resolución horaria con almacenamiento de energía
- **🌱 Ciclo de Vida**: Análisis completo de emisiones de construcción y operación
- **📱 Interfaz Moderna**: GUI intuitiva con visualizaciones interactivas
- **💾 Base de Datos**: Parámetros técnico-económicos actualizables

## 🚀 Instalación Rápida

```bash
# Clonar repositorio
git clone <repository-url>
cd mejoras_proyecto

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
python main.py
```

## 📖 Uso

### Interfaz Gráfica
```bash
python main.py
```

### Línea de Comandos
```bash
python main.py --config config/default.yaml --output results/
```

### Como Librería
```python
from src.optimizacion import OptimizadorEnergetico

optimizador = OptimizadorEnergetico()
resultado = optimizador.optimizar()
```

## 🏗️ Arquitectura

```
mejoras_proyecto/
├── src/                    # Código fuente
│   ├── modelos/           # Modelos matemáticos
│   ├── optimizacion/      # Algoritmos de optimización
│   ├── gui/              # Interfaz gráfica
│   └── utils/            # Utilidades
├── config/               # Archivos de configuración
├── data/                # Datos y parámetros
├── tests/               # Pruebas automatizadas
└── examples/            # Ejemplos de uso
```

## 📊 Métodos de Optimización

- **Lexicográfico**: Optimización jerárquica por prioridades
- **Ponderación**: Combinación lineal de objetivos
- **ε-restricción**: Optimización con restricciones parametrizadas
- **NSGA-II**: Algoritmo genético multiobjetivo
- **TOPSIS**: Técnica de ordenamiento por proximidad al ideal

## 🔬 Validación

El sistema incluye casos de prueba basados en:
- Datos de literatura científica
- Casos extremos y límite
- Validación cruzada con software comercial

## 📈 Resultados

- Gráficas Pareto 3D interactivas
- Reportes automáticos en PDF/Excel
- Análisis de sensibilidad detallado
- Mapas de calor de trade-offs

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:
1. Fork del proyecto
2. Crear branch para nueva característica
3. Commit de cambios
4. Push al branch
5. Crear Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.

## 👨‍💻 Autor

Ing. Sergio Isaías Silva Márquez
- Proyecto de Maestría en Ingeniería Energética
- Versión mejorada con optimizaciones avanzadas

## 📚 Referencias

- Ramakumar, R. (1986). Engineering Reliability: New Techniques and Applications
- Coello, C. A. C. (2006). Evolutionary Algorithms for Solving Multi-Objective Problems
- Deb, K. (2001). Multi-Objective Optimization using Evolutionary Algorithms
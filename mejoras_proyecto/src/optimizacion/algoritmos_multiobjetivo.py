"""
Algoritmos multiobjetivo: NSGA-II y TOPSIS
"""

import numpy as np
from typing import List, Tuple, Dict, Any
import random

class NSGA2:
    """
    Implementación simplificada del algoritmo NSGA-II
    """
    
    def __init__(self, modelo, poblacion=100, generaciones=50, prob_cruce=0.9, prob_mutacion=0.1):
        self.modelo = modelo
        self.poblacion = poblacion
        self.generaciones = generaciones
        self.prob_cruce = prob_cruce
        self.prob_mutacion = prob_mutacion
        
    def optimizar(self) -> Tuple[List, List, List]:
        """
        Ejecuta NSGA-II (versión simplificada para demostración)
        
        Returns:
            Tuple (frente_pareto, poblacion_final, convergencia)
        """
        
        # Inicializar población aleatoria
        poblacion = self._inicializar_poblacion()
        
        convergencia = []
        
        for gen in range(self.generaciones):
            # Evaluar población
            for individuo in poblacion:
                individuo.fitness = self._evaluar_individuo(individuo)
                
            # Selección, cruce y mutación (simplificado)
            nueva_poblacion = self._evolucionar_poblacion(poblacion)
            poblacion = nueva_poblacion
            
            # Registrar convergencia
            if poblacion:
                mejor_fitness = min([ind.fitness.values[0] for ind in poblacion])
                convergencia.append(mejor_fitness)
                
        # Extraer frente Pareto
        frente_pareto = self._extraer_frente_pareto(poblacion)
        
        return frente_pareto, poblacion, convergencia
        
    def _inicializar_poblacion(self) -> List:
        """Inicializa población aleatoria"""
        poblacion = []
        
        n_recursos = len(self.modelo.recursos)
        n_tareas = len(self.modelo.tareas)
        
        for _ in range(self.poblacion):
            # Crear individuo como array de asignaciones
            individuo = type('Individuo', (), {})()
            individuo.genes = np.random.rand(n_recursos, n_tareas) * 1000
            individuo.fitness = None
            poblacion.append(individuo)
            
        return poblacion
        
    def _evaluar_individuo(self, individuo) -> type:
        """Evalúa un individuo (simplificado)"""
        
        # Simular evaluación de las 3 funciones objetivo
        genes = individuo.genes
        
        # Función objetivo 1: Costo (a minimizar)
        costo = np.sum(genes) * 0.1
        
        # Función objetivo 2: Emisiones CO2 (a minimizar)  
        emisiones = np.sum(genes) * 0.05
        
        # Función objetivo 3: Factor social (a maximizar, convertir a minimizar)
        social = -np.mean(genes) * 0.01
        
        # Crear objeto fitness
        fitness = type('Fitness', (), {})()
        fitness.values = [costo, emisiones, social]
        
        return fitness
        
    def _evolucionar_poblacion(self, poblacion) -> List:
        """Evoluciona la población (simplificado)"""
        
        # Mantener misma población para esta demostración
        nueva_poblacion = []
        
        for i in range(len(poblacion)):
            # Seleccionar padres aleatoriamente
            padre1 = random.choice(poblacion)
            padre2 = random.choice(poblacion)
            
            # Cruce simple
            hijo = self._cruce(padre1, padre2)
            
            # Mutación
            if random.random() < self.prob_mutacion:
                hijo = self._mutar(hijo)
                
            nueva_poblacion.append(hijo)
            
        return nueva_poblacion
        
    def _cruce(self, padre1, padre2):
        """Operador de cruce"""
        hijo = type('Individuo', (), {})()
        
        # Cruce uniforme
        mask = np.random.rand(*padre1.genes.shape) < 0.5
        hijo.genes = np.where(mask, padre1.genes, padre2.genes)
        hijo.fitness = None
        
        return hijo
        
    def _mutar(self, individuo):
        """Operador de mutación"""
        # Mutación gaussiana
        individuo.genes += np.random.normal(0, 0.1, individuo.genes.shape)
        individuo.genes = np.clip(individuo.genes, 0, None)  # No negativos
        
        return individuo
        
    def _extraer_frente_pareto(self, poblacion) -> List:
        """Extrae frente Pareto de la población"""
        
        if not poblacion:
            return []
            
        # Filtrar individuos no dominados (simplificado)
        frente_pareto = []
        
        for i, ind1 in enumerate(poblacion):
            es_dominado = False
            
            for j, ind2 in enumerate(poblacion):
                if i != j and self._domina(ind2, ind1):
                    es_dominado = True
                    break
                    
            if not es_dominado:
                frente_pareto.append(ind1)
                
        return frente_pareto
        
    def _domina(self, ind1, ind2) -> bool:
        """Verifica si ind1 domina a ind2"""
        if not (ind1.fitness and ind2.fitness):
            return False
            
        # ind1 domina ind2 si es mejor o igual en todos los objetivos
        # y estrictamente mejor en al menos uno
        mejor_o_igual = all(v1 <= v2 for v1, v2 in zip(ind1.fitness.values, ind2.fitness.values))
        estrictamente_mejor = any(v1 < v2 for v1, v2 in zip(ind1.fitness.values, ind2.fitness.values))
        
        return mejor_o_igual and estrictamente_mejor

class AlgoritmoTOPSIS:
    """
    Implementación del método TOPSIS para selección de alternativas
    """
    
    def calcular_ranking(self, matriz_decision: np.ndarray, 
                        pesos: List[float], 
                        criterios: List[str]) -> Tuple[List[int], List[float]]:
        """
        Calcula ranking usando TOPSIS
        
        Args:
            matriz_decision: Matriz de alternativas vs criterios
            pesos: Pesos de los criterios
            criterios: Tipo de criterio ('min' o 'max')
            
        Returns:
            Tuple (ranking_indices, scores)
        """
        
        # Paso 1: Normalizar matriz de decisión
        matriz_normalizada = self._normalizar_matriz(matriz_decision)
        
        # Paso 2: Aplicar pesos
        matriz_ponderada = matriz_normalizada * np.array(pesos)
        
        # Paso 3: Determinar soluciones ideales
        solucion_ideal_positiva = []
        solucion_ideal_negativa = []
        
        for j, criterio in enumerate(criterios):
            if criterio == 'max':
                solucion_ideal_positiva.append(np.max(matriz_ponderada[:, j]))
                solucion_ideal_negativa.append(np.min(matriz_ponderada[:, j]))
            else:  # 'min'
                solucion_ideal_positiva.append(np.min(matriz_ponderada[:, j]))
                solucion_ideal_negativa.append(np.max(matriz_ponderada[:, j]))
                
        # Paso 4: Calcular distancias
        distancias_positivas = []
        distancias_negativas = []
        
        for i in range(matriz_ponderada.shape[0]):
            d_pos = np.sqrt(np.sum((matriz_ponderada[i] - solucion_ideal_positiva)**2))
            d_neg = np.sqrt(np.sum((matriz_ponderada[i] - solucion_ideal_negativa)**2))
            
            distancias_positivas.append(d_pos)
            distancias_negativas.append(d_neg)
            
        # Paso 5: Calcular scores de proximidad
        scores = []
        for d_pos, d_neg in zip(distancias_positivas, distancias_negativas):
            if d_pos + d_neg == 0:
                score = 0.5
            else:
                score = d_neg / (d_pos + d_neg)
            scores.append(score)
            
        # Paso 6: Crear ranking
        ranking = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        
        return ranking, scores
        
    def _normalizar_matriz(self, matriz: np.ndarray) -> np.ndarray:
        """Normaliza la matriz de decisión usando normalización vectorial"""
        
        matriz_normalizada = np.zeros_like(matriz, dtype=float)
        
        for j in range(matriz.shape[1]):
            columna = matriz[:, j]
            norma = np.sqrt(np.sum(columna**2))
            
            if norma > 0:
                matriz_normalizada[:, j] = columna / norma
            else:
                matriz_normalizada[:, j] = 0
                
        return matriz_normalizada
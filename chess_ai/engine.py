from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

import chess

from chess_ai.evaluation import Evaluator
from chess_ai.search import SearchResult, find_best_move


class Level(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


@dataclass(frozen=True)
class EngineConfig:
    level: Level
    depth: int
    random_probability: float


LEVELS = {
    Level.EASY: EngineConfig(level=Level.EASY, depth=1, random_probability=0.35),
    Level.MEDIUM: EngineConfig(level=Level.MEDIUM, depth=3, random_probability=0.03),
    Level.HARD: EngineConfig(level=Level.HARD, depth=4, random_probability=0.0),
}


class ChessEngine:
    def __init__(self, evaluator: Evaluator, level: Level = Level.MEDIUM, seed: int | None = None) -> None:
        self.evaluator = evaluator
        self.config = LEVELS[level]
        self.random = random.Random(seed)

    def choose_move(self, board: chess.Board) -> SearchResult:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            raise ValueError("No legal moves available.")

        if self.random.random() < self.config.random_probability:
            move = self.random.choice(legal_moves)
            return SearchResult(move=move, score=self.evaluator.evaluate(board), nodes=1)

        return find_best_move(board, depth=self.config.depth, evaluator=self.evaluator)

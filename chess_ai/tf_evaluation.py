from __future__ import annotations

import chess
import numpy as np
import tensorflow as tf

from chess_ai.board_encoding import encode_board
from chess_ai.evaluation import material_score, terminal_score


class TensorFlowEvaluator:
    """Evaluator compatible with the engine, backed by a TensorFlow model."""

    def __init__(self, model: tf.keras.Model, neural_weight: float = 0.55) -> None:
        self.model = model
        self.neural_weight = neural_weight

    def evaluate(self, board: chess.Board) -> float:
        terminal = terminal_score(board)
        if terminal is not None:
            return terminal

        material = material_score(board)
        encoded = np.expand_dims(encode_board(board), axis=0).astype(np.float32)
        neural = float(self.model.predict(encoded, verbose=0)[0][0])
        return (self.neural_weight * neural) + ((1.0 - self.neural_weight) * material)

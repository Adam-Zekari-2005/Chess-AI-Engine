from __future__ import annotations

import math
from dataclasses import dataclass, field

import chess

from chess_ai.evaluation import Evaluator


CAPTURE_BONUS = 10_000
PROMOTION_BONUS = 8_000
CHECK_BONUS = 1_000
KILLER_BONUS = 700
MAX_QUIESCENCE_DEPTH = 5


@dataclass(frozen=True)
class SearchResult:
    move: chess.Move
    score: float
    nodes: int


@dataclass
class SearchContext:
    evaluator: Evaluator
    transposition: dict[tuple[str, int], float] = field(default_factory=dict)
    killer_moves: dict[int, list[chess.Move]] = field(default_factory=dict)


def ordered_moves(board: chess.Board, ply: int = 0, context: SearchContext | None = None) -> list[chess.Move]:
    moves = list(board.legal_moves)
    killers = context.killer_moves.get(ply, []) if context else []

    def move_score(move: chess.Move) -> int:
        score = 0
        if move in killers:
            score += KILLER_BONUS
        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                score += CAPTURE_BONUS + (victim.piece_type * 100) - attacker.piece_type
            else:
                score += CAPTURE_BONUS
        if move.promotion:
            score += PROMOTION_BONUS
        board.push(move)
        if board.is_check():
            score += CHECK_BONUS
        board.pop()
        return score

    moves.sort(key=move_score, reverse=True)
    return moves


def quiescence(
    board: chess.Board,
    alpha: float,
    beta: float,
    context: SearchContext,
    depth: int = 0,
) -> tuple[float, int]:
    stand_pat = context.evaluator.evaluate(board)
    nodes = 1

    if board.turn == chess.WHITE:
        if stand_pat >= beta:
            return beta, nodes
        alpha = max(alpha, stand_pat)
    else:
        if stand_pat <= alpha:
            return alpha, nodes
        beta = min(beta, stand_pat)

    if depth >= MAX_QUIESCENCE_DEPTH:
        return stand_pat, nodes

    noisy_moves = [move for move in ordered_moves(board, context=context) if board.is_capture(move) or move.promotion]
    for move in noisy_moves:
        board.push(move)
        score, child_nodes = quiescence(board, alpha, beta, context, depth + 1)
        board.pop()
        nodes += child_nodes

        if board.turn == chess.WHITE:
            alpha = max(alpha, score)
            if alpha >= beta:
                break
        else:
            beta = min(beta, score)
            if beta <= alpha:
                break

    return (alpha if board.turn == chess.WHITE else beta), nodes


def minimax(
    board: chess.Board,
    depth: int,
    alpha: float,
    beta: float,
    context: SearchContext,
    ply: int = 0,
) -> tuple[float, int]:
    if board.is_game_over(claim_draw=True):
        return context.evaluator.evaluate(board), 1
    if depth == 0:
        return quiescence(board, alpha, beta, context)

    key = (board.transposition_key() if hasattr(board, "transposition_key") else board.fen(), depth)
    cached = context.transposition.get(key)
    if cached is not None:
        return cached, 1

    nodes = 1
    if board.turn == chess.WHITE:
        best_score = -math.inf
        for move in ordered_moves(board, ply, context):
            board.push(move)
            score, child_nodes = minimax(board, depth - 1, alpha, beta, context, ply + 1)
            board.pop()
            nodes += child_nodes
            best_score = max(best_score, score)
            alpha = max(alpha, score)
            if beta <= alpha:
                context.killer_moves.setdefault(ply, []).append(move)
                break
        context.transposition[key] = best_score
        return best_score, nodes

    best_score = math.inf
    for move in ordered_moves(board, ply, context):
        board.push(move)
        score, child_nodes = minimax(board, depth - 1, alpha, beta, context, ply + 1)
        board.pop()
        nodes += child_nodes
        best_score = min(best_score, score)
        beta = min(beta, score)
        if beta <= alpha:
            context.killer_moves.setdefault(ply, []).append(move)
            break
    context.transposition[key] = best_score
    return best_score, nodes


def find_best_move(board: chess.Board, depth: int, evaluator: Evaluator) -> SearchResult:
    context = SearchContext(evaluator=evaluator)
    best_move: chess.Move | None = None
    best_score = -math.inf if board.turn == chess.WHITE else math.inf
    total_nodes = 0

    for current_depth in range(1, depth + 1):
        best_move = None
        best_score = -math.inf if board.turn == chess.WHITE else math.inf

        for move in ordered_moves(board, context=context):
            board.push(move)
            score, nodes = minimax(board, current_depth - 1, -math.inf, math.inf, context, 1)
            board.pop()
            total_nodes += nodes

            if board.turn == chess.WHITE and score > best_score:
                best_score = score
                best_move = move
            elif board.turn == chess.BLACK and score < best_score:
                best_score = score
                best_move = move

    if best_move is None:
        raise ValueError("No legal moves available.")
    return SearchResult(move=best_move, score=best_score, nodes=total_nodes)

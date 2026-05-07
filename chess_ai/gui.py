from __future__ import annotations

import argparse
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

import chess

from chess_ai.engine import ChessEngine, Level
from chess_ai.evaluation import Evaluator
from chess_ai.model import load_model


SQUARE_SIZE = 72
LIGHT = "#e9dcc5"
DARK = "#7b6f62"
SELECTED = "#d9b45f"
LAST_MOVE = "#b8a46f"
LEGAL_DOT = "#2f2f2f"
WHITE_PIECE = "#f8f5ee"
BLACK_PIECE = "#1f1f1f"


def piece_text(piece: chess.Piece | None) -> str:
    return "" if piece is None else piece.unicode_symbol()


class ChessApp:
    def __init__(self, root: tk.Tk, model_path: str | None = None, backend: str = "pytorch") -> None:
        self.root = root
        self.root.title("Chess AI")
        self.board = chess.Board()
        self.selected_square: chess.Square | None = None
        self.last_move: chess.Move | None = None
        self.human_color = chess.WHITE
        self.model_path = model_path
        self.backend = backend
        self.evaluator = self._load_evaluator(model_path, backend)
        self.engine = ChessEngine(self.evaluator, Level.MEDIUM)
        self.canvas: tk.Canvas

        self.level_var = tk.StringVar(value=Level.MEDIUM.value)
        self.color_var = tk.StringVar(value="white")
        self.status_var = tk.StringVar(value="Choose options, then play.")

        self._build_layout()
        self._render_board()

    def _load_evaluator(self, model_path: str | None, backend: str) -> Evaluator:
        if model_path is None:
            return Evaluator(model=None)
        if not Path(model_path).exists():
            messagebox.showwarning(
                "Model not found",
                f"Model file not found:\n{model_path}\n\nThe game will start without a trained model.",
            )
            return Evaluator(model=None)
        if backend == "tensorflow":
            from chess_ai.tf_evaluation import TensorFlowEvaluator
            from chess_ai.tf_model import load_tf_model

            return TensorFlowEvaluator(model=load_tf_model(model_path))  # type: ignore[return-value]
        return Evaluator(model=load_model(model_path))

    def _build_layout(self) -> None:
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill="x")

        ttk.Label(top, text="Level").pack(side="left")
        level_menu = ttk.Combobox(
            top,
            values=[level.value for level in Level],
            textvariable=self.level_var,
            state="readonly",
            width=10,
        )
        level_menu.pack(side="left", padx=(6, 14))
        level_menu.bind("<<ComboboxSelected>>", lambda _: self._update_engine())

        ttk.Label(top, text="You play").pack(side="left")
        color_menu = ttk.Combobox(
            top,
            values=["white", "black"],
            textvariable=self.color_var,
            state="readonly",
            width=10,
        )
        color_menu.pack(side="left", padx=(6, 14))
        color_menu.bind("<<ComboboxSelected>>", lambda _: self.new_game())

        ttk.Button(top, text="New game", command=self.new_game).pack(side="left")

        self.canvas = tk.Canvas(
            self.root,
            width=SQUARE_SIZE * 8,
            height=SQUARE_SIZE * 8,
            highlightthickness=0,
            bg=LIGHT,
        )
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        ttk.Label(self.root, textvariable=self.status_var, padding=(10, 0, 10, 10)).pack(fill="x")

    def _square_from_view(self, row: int, col: int) -> chess.Square:
        if self.human_color == chess.WHITE:
            rank = 7 - row
            file_index = col
        else:
            rank = row
            file_index = 7 - col
        return chess.square(file_index, rank)

    def _update_engine(self) -> None:
        self.engine = ChessEngine(self.evaluator, Level(self.level_var.get()))
        self.status_var.set(f"Level set to {self.level_var.get()}.")

    def new_game(self) -> None:
        self.board = chess.Board()
        self.selected_square = None
        self.last_move = None
        self.human_color = chess.WHITE if self.color_var.get() == "white" else chess.BLACK
        self._update_engine()
        self._render_board()
        if self.board.turn != self.human_color:
            self.root.after(300, self.ai_move)

    def on_canvas_click(self, event: tk.Event) -> None:
        col = int(event.x // SQUARE_SIZE)
        row = int(event.y // SQUARE_SIZE)
        if 0 <= row < 8 and 0 <= col < 8:
            self.on_square_click(self._square_from_view(row, col))

    def on_square_click(self, square: chess.Square) -> None:
        if self.board.is_game_over(claim_draw=True) or self.board.turn != self.human_color:
            return

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece is not None and piece.color == self.human_color:
                self.selected_square = square
                self._render_board()
            return

        move = chess.Move(self.selected_square, square)
        if self._is_promotion(move):
            move = chess.Move(self.selected_square, square, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            self.board.push(move)
            self.last_move = move
            self.selected_square = None
            self._render_board()
            self._finish_or_schedule_ai()
        else:
            self.selected_square = None
            self._render_board()

    def _is_promotion(self, move: chess.Move) -> bool:
        piece = self.board.piece_at(move.from_square)
        if piece is None or piece.piece_type != chess.PAWN:
            return False
        target_rank = chess.square_rank(move.to_square)
        return target_rank in {0, 7}

    def _finish_or_schedule_ai(self) -> None:
        if self.board.is_game_over(claim_draw=True):
            self._show_game_over()
        else:
            self.status_var.set("AI is thinking...")
            self.root.after(300, self.ai_move)

    def ai_move(self) -> None:
        if self.board.is_game_over(claim_draw=True) or self.board.turn == self.human_color:
            return
        result = self.engine.choose_move(self.board)
        self.board.push(result.move)
        self.last_move = result.move
        self.status_var.set(f"AI played {result.move.uci()} | score={result.score:.3f} | nodes={result.nodes}")
        self._render_board()
        if self.board.is_game_over(claim_draw=True):
            self._show_game_over()

    def _render_board(self) -> None:
        self.canvas.delete("all")
        for view_row in range(8):
            for view_col in range(8):
                square = self._square_from_view(view_row, view_col)
                piece = self.board.piece_at(square)
                color = LIGHT if (chess.square_rank(square) + chess.square_file(square)) % 2 else DARK
                x1 = view_col * SQUARE_SIZE
                y1 = view_row * SQUARE_SIZE
                x2 = x1 + SQUARE_SIZE
                y2 = y1 + SQUARE_SIZE

                if self.last_move and square in {self.last_move.from_square, self.last_move.to_square}:
                    color = LAST_MOVE
                if self.selected_square == square:
                    color = SELECTED

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=color)

                if self._is_legal_target(square):
                    radius = 7 if piece is None else 11
                    self.canvas.create_oval(
                        x1 + SQUARE_SIZE / 2 - radius,
                        y1 + SQUARE_SIZE / 2 - radius,
                        x1 + SQUARE_SIZE / 2 + radius,
                        y1 + SQUARE_SIZE / 2 + radius,
                        fill=LEGAL_DOT if piece is None else "",
                        outline=LEGAL_DOT,
                        width=2,
                    )

                if piece is not None:
                    self.canvas.create_text(
                        x1 + SQUARE_SIZE / 2,
                        y1 + SQUARE_SIZE / 2,
                        text=piece_text(piece),
                        font=("Segoe UI Symbol", 38),
                        fill=WHITE_PIECE if piece.color == chess.WHITE else BLACK_PIECE,
                    )

    def _is_legal_target(self, square: chess.Square) -> bool:
        if self.selected_square is None:
            return False
        candidate = chess.Move(self.selected_square, square)
        if self._is_promotion(candidate):
            candidate = chess.Move(self.selected_square, square, promotion=chess.QUEEN)
        return candidate in self.board.legal_moves

    def _show_game_over(self) -> None:
        result = self.board.result(claim_draw=True)
        self.status_var.set(f"Game over: {result}")
        messagebox.showinfo("Game over", f"Result: {result}\n{self.board.outcome(claim_draw=True)}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Graphical chess game against the AI.")
    parser.add_argument("--backend", choices=["pytorch", "tensorflow"], default="pytorch")
    parser.add_argument("--model", default=None, help="Optional path to a trained model.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = tk.Tk()
    ChessApp(root, model_path=args.model, backend=args.backend)
    root.mainloop()


if __name__ == "__main__":
    main()

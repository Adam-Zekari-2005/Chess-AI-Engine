import chess

from chess_ai.board_encoding import encode_board, result_to_value


def test_starting_position_encoding_shape_and_piece_count():
    board = chess.Board()
    encoded = encode_board(board)
    assert encoded.shape == (18, 8, 8)
    assert encoded[:12].sum() == 32


def test_result_to_value():
    assert result_to_value("1-0") == 1.0
    assert result_to_value("0-1") == -1.0
    assert result_to_value("1/2-1/2") == 0.0

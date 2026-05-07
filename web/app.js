const START_POSITION = {
  a8: "\u265c", b8: "\u265e", c8: "\u265d", d8: "\u265b", e8: "\u265a", f8: "\u265d", g8: "\u265e", h8: "\u265c",
  a7: "\u265f", b7: "\u265f", c7: "\u265f", d7: "\u265f", e7: "\u265f", f7: "\u265f", g7: "\u265f", h7: "\u265f",
  a2: "\u2659", b2: "\u2659", c2: "\u2659", d2: "\u2659", e2: "\u2659", f2: "\u2659", g2: "\u2659", h2: "\u2659",
  a1: "\u2656", b1: "\u2658", c1: "\u2657", d1: "\u2655", e1: "\u2654", f1: "\u2657", g1: "\u2658", h1: "\u2656",
};

const WHITE_PIECES = new Set(["\u2654", "\u2655", "\u2656", "\u2657", "\u2658", "\u2659"]);
const PIECE_VALUE = {
  "\u2659": 100, "\u2658": 320, "\u2657": 330, "\u2656": 500, "\u2655": 900, "\u2654": 20000,
  "\u265f": 100, "\u265e": 320, "\u265d": 330, "\u265c": 500, "\u265b": 900, "\u265a": 20000,
};
const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
const ranks = ["8", "7", "6", "5", "4", "3", "2", "1"];
const levelDepth = { Facile: 1, Moyen: 2, Difficile: 3 };

let boardState = { ...START_POSITION };
let selected = null;
let turn = "white";
let gameMode = "ai";
let onlineColor = "white";
let socket = null;
let currentRoom = null;
let pendingMessages = [];
let selectedAvatar = { name: "Chevalier", style: "avatar-knight", letter: "C" };
let currentUser = {
  username: "Joueur",
  avatar: selectedAvatar,
  games: 0,
  friends: [],
};

const screens = {
  home: document.querySelector("#homeScreen"),
  info: document.querySelector("#infoScreen"),
  auth: document.querySelector("#authScreen"),
  game: document.querySelector("#gameScreen"),
};

const floatingBoard = document.querySelector("#floatingBoard");
const demoBoard = document.querySelector("#demoBoard");
const moveStatus = document.querySelector("#moveStatus");
const levelLabel = document.querySelector("#levelLabel");
const resetBoard = document.querySelector("#resetBoard");
const authMessage = document.querySelector("#authMessage");
const playerName = document.querySelector("#playerName");
const headerAvatar = document.querySelector("#headerAvatar");
const profileAvatar = document.querySelector("#profileAvatar");
const profileTitle = document.querySelector("#profileTitle");
const profileSubtitle = document.querySelector("#profileSubtitle");
const statGames = document.querySelector("#statGames");
const statMode = document.querySelector("#statMode");
const onlinePanel = document.querySelector("#onlinePanel");
const roomInput = document.querySelector("#roomInput");
const roomStatus = document.querySelector("#roomStatus");
const chatMessages = document.querySelector("#chatMessages");
const chatInput = document.querySelector("#chatInput");
const friendInput = document.querySelector("#friendInput");
const addFriendButton = document.querySelector("#addFriendButton");
const friendList = document.querySelector("#friendList");
const inviteNotice = document.querySelector("#inviteNotice");
const privateTarget = document.querySelector("#privateTarget");
const privateInput = document.querySelector("#privateInput");
const privateMessages = document.querySelector("#privateMessages");

const savedTheme = localStorage.getItem("chessAiTheme") || "light";
setTheme(savedTheme);

if (localStorage.getItem("deepChessUser")) localStorage.removeItem("deepChessUser");

function saveCurrentUser() {
  localStorage.setItem("chessAiUser", JSON.stringify(currentUser));
}

function normalizeAvatar(avatar) {
  if (avatar && typeof avatar === "object") return avatar;
  return { name: "Chevalier", style: "avatar-knight", letter: "C" };
}

function renderAvatar(element, avatar, extraClass) {
  const normalized = normalizeAvatar(avatar);
  element.className = `character-avatar ${extraClass} ${normalized.style}`;
  element.textContent = normalized.letter;
  element.title = normalized.name;
}

function updateProfile() {
  playerName.textContent = currentUser.username || "Joueur";
  renderAvatar(headerAvatar, currentUser.avatar, "mini-avatar");
  renderAvatar(profileAvatar, currentUser.avatar, "profile-avatar");
  profileTitle.textContent = currentUser.username || "Joueur";
  profileSubtitle.textContent = gameMode === "online"
    ? "Profil pret pour une partie en ligne."
    : "Profil pret pour affronter l'IA.";
  statGames.textContent = String(currentUser.games || 0);
  statMode.textContent = gameMode === "online" ? "Ami" : "IA";
  renderFriends();
}

function setTheme(theme) {
  document.body.dataset.theme = theme;
  localStorage.setItem("chessAiTheme", theme);
  document.querySelectorAll(".theme-choice").forEach((button) => {
    button.classList.toggle("active", button.dataset.theme === theme);
  });
}

function addPrivateMessage(author, text) {
  const div = document.createElement("div");
  div.className = "private-message";
  div.textContent = `${author}: ${text}`;
  privateMessages.append(div);
  privateMessages.scrollTop = privateMessages.scrollHeight;
}

function renderFriends() {
  if (!friendList) return;
  friendList.innerHTML = "";
  (currentUser.friends || []).forEach((friend) => {
    const chip = document.createElement("span");
    chip.className = "friend-chip";
    chip.textContent = friend;

    const invite = document.createElement("button");
    invite.type = "button";
    invite.textContent = "Inviter";
    invite.addEventListener("click", () => inviteFriend(friend));

    const dm = document.createElement("button");
    dm.type = "button";
    dm.textContent = "MP";
    dm.addEventListener("click", () => {
      privateTarget.value = friend;
      privateInput.focus();
    });

    chip.append(invite, dm);
    friendList.append(chip);
  });
}

function addFriend(name) {
  const friend = name.trim();
  if (!friend || friend === currentUser.username) return;
  currentUser.friends = currentUser.friends || [];
  if (!currentUser.friends.includes(friend)) currentUser.friends.push(friend);
  saveCurrentUser();
  renderFriends();
}

function inviteFriend(friend) {
  gameMode = "online";
  document.querySelectorAll(".mode-control").forEach((item) => {
    item.classList.toggle("active", item.dataset.mode === "online");
  });
  onlinePanel.classList.remove("hidden");
  const room = `room-${currentUser.username}-${friend}`.replace(/\s+/g, "-").toLowerCase();
  roomInput.value = room;
  if (!socket || socket.readyState !== WebSocket.OPEN || currentRoom !== room) connectOnlineRoom();
  sendOnline({ type: "invite", to: friend, from: currentUser.username, room });
  addPrivateMessage("Systeme", `Invitation envoyee a ${friend} pour le salon ${room}.`);
}

function showScreen(name) {
  Object.values(screens).forEach((screen) => screen.classList.add("hidden"));
  screens[name].classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showLanding() {
  Object.values(screens).forEach((screen) => screen.classList.add("hidden"));
  screens.home.classList.remove("hidden");
  screens.info.classList.remove("hidden");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function squareName(fileIndex, rankIndex) {
  return `${files[fileIndex]}${ranks[rankIndex]}`;
}

function fileIndex(square) {
  return files.indexOf(square[0]);
}

function rankNumber(square) {
  return Number(square[1]);
}

function makeSquare(file, rank) {
  if (file < 0 || file > 7 || rank < 1 || rank > 8) return null;
  return `${files[file]}${rank}`;
}

function isWhitePiece(piece) {
  return WHITE_PIECES.has(piece);
}

function colorOf(piece) {
  if (!piece) return null;
  return isWhitePiece(piece) ? "white" : "black";
}

function isOwnPiece(piece, color) {
  return piece && colorOf(piece) === color;
}

function isEnemyPiece(piece, color) {
  return piece && colorOf(piece) !== color;
}

function isLight(file, rankIndex) {
  return (file + rankIndex) % 2 === 0;
}

function addRayMoves(board, square, color, directions, moves) {
  const startFile = fileIndex(square);
  const startRank = rankNumber(square);
  directions.forEach(([df, dr]) => {
    let f = startFile + df;
    let r = startRank + dr;
    while (true) {
      const target = makeSquare(f, r);
      if (!target) break;
      if (!board[target]) {
        moves.push(target);
      } else {
        if (isEnemyPiece(board[target], color)) moves.push(target);
        break;
      }
      f += df;
      r += dr;
    }
  });
}

function legalMovesFrom(square, board = boardState) {
  const piece = board[square];
  const color = colorOf(piece);
  if (!piece || !color) return [];

  const file = fileIndex(square);
  const rank = rankNumber(square);
  const moves = [];
  const lower = piece.toLowerCase();

  if (piece === "\u2659" || piece === "\u265f") {
    const direction = color === "white" ? 1 : -1;
    const startRank = color === "white" ? 2 : 7;
    const oneStep = makeSquare(file, rank + direction);
    const twoSteps = makeSquare(file, rank + direction * 2);
    if (oneStep && !board[oneStep]) moves.push(oneStep);
    if (rank === startRank && oneStep && twoSteps && !board[oneStep] && !board[twoSteps]) moves.push(twoSteps);
    [file - 1, file + 1].forEach((targetFile) => {
      const target = makeSquare(targetFile, rank + direction);
      if (target && isEnemyPiece(board[target], color)) moves.push(target);
    });
  }

  if (piece === "\u2658" || piece === "\u265e") {
    [[1, 2], [2, 1], [-1, 2], [-2, 1], [1, -2], [2, -1], [-1, -2], [-2, -1]].forEach(([df, dr]) => {
      const target = makeSquare(file + df, rank + dr);
      if (target && !isOwnPiece(board[target], color)) moves.push(target);
    });
  }

  if (piece === "\u2657" || piece === "\u265d") addRayMoves(board, square, color, [[1, 1], [1, -1], [-1, 1], [-1, -1]], moves);
  if (piece === "\u2656" || piece === "\u265c") addRayMoves(board, square, color, [[1, 0], [-1, 0], [0, 1], [0, -1]], moves);
  if (piece === "\u2655" || piece === "\u265b") addRayMoves(board, square, color, [[1, 1], [1, -1], [-1, 1], [-1, -1], [1, 0], [-1, 0], [0, 1], [0, -1]], moves);

  if (piece === "\u2654" || piece === "\u265a") {
    [[1, 1], [1, 0], [1, -1], [0, 1], [0, -1], [-1, 1], [-1, 0], [-1, -1]].forEach(([df, dr]) => {
      const target = makeSquare(file + df, rank + dr);
      if (target && !isOwnPiece(board[target], color)) moves.push(target);
    });
  }

  return moves;
}

function allLegalMoves(color, board = boardState) {
  return Object.keys(board).flatMap((from) => {
    if (colorOf(board[from]) !== color) return [];
    return legalMovesFrom(from, board).map((to) => ({ from, to }));
  });
}

function applyMove(board, move) {
  const next = { ...board };
  next[move.to] = next[move.from];
  delete next[move.from];
  return next;
}

function evaluateBoard(board) {
  let score = 0;
  Object.entries(board).forEach(([square, piece]) => {
    const value = PIECE_VALUE[piece] || 0;
    const centerBonus = 8 - Math.abs(fileIndex(square) - 3.5) - Math.abs(rankNumber(square) - 4.5);
    const signed = isWhitePiece(piece) ? value + centerBonus * 2 : -(value + centerBonus * 2);
    score += signed;
  });
  score += allLegalMoves("white", board).length * 3;
  score -= allLegalMoves("black", board).length * 3;
  return score;
}

function minimax(board, depth, maximizing, alpha, beta) {
  const color = maximizing ? "white" : "black";
  const moves = allLegalMoves(color, board);
  if (depth === 0 || moves.length === 0) return evaluateBoard(board);

  if (maximizing) {
    let best = -Infinity;
    for (const move of moves) {
      best = Math.max(best, minimax(applyMove(board, move), depth - 1, false, alpha, beta));
      alpha = Math.max(alpha, best);
      if (beta <= alpha) break;
    }
    return best;
  }

  let best = Infinity;
  for (const move of moves) {
    best = Math.min(best, minimax(applyMove(board, move), depth - 1, true, alpha, beta));
    beta = Math.min(beta, best);
    if (beta <= alpha) break;
  }
  return best;
}

function chooseAiMove() {
  const moves = allLegalMoves("black");
  const depth = levelDepth[levelLabel.textContent] || 1;
  let bestMove = moves[0];
  let bestScore = Infinity;
  for (const move of moves) {
    const captureBonus = isWhitePiece(boardState[move.to]) ? -PIECE_VALUE[boardState[move.to]] : 0;
    const score = minimax(applyMove(boardState, move), depth - 1, true, -Infinity, Infinity) + captureBonus;
    if (score < bestScore) {
      bestScore = score;
      bestMove = move;
    }
  }
  return bestMove;
}

function buildFloatingBoard() {
  floatingBoard.innerHTML = "";
  ranks.forEach((_, rankIndex) => {
    files.forEach((_, file) => {
      const square = squareName(file, rankIndex);
      const tile = document.createElement("div");
      tile.className = `tile ${isLight(file, rankIndex) ? "light" : "dark"}`;
      if (START_POSITION[square]) {
        const piece = document.createElement("span");
        piece.className = `piece ${isWhitePiece(START_POSITION[square]) ? "white-piece" : "black-piece"}`;
        piece.textContent = START_POSITION[square];
        tile.append(piece);
      }
      floatingBoard.append(tile);
    });
  });
}

function buildDemoBoard() {
  demoBoard.innerHTML = "";
  ranks.forEach((_, rankIndex) => {
    files.forEach((_, file) => {
      const square = squareName(file, rankIndex);
      const tile = document.createElement("button");
      tile.type = "button";
      tile.className = `tile ${isLight(file, rankIndex) ? "light" : "dark"}`;
      if (boardState[square]) {
        const piece = document.createElement("span");
        piece.className = `piece ${isWhitePiece(boardState[square]) ? "white-piece" : "black-piece"}`;
        piece.textContent = boardState[square];
        tile.append(piece);
      }
      if (selected === square) tile.classList.add("selected");
      if (selected && legalMovesFrom(selected).includes(square)) tile.classList.add("legal");
      tile.addEventListener("click", () => handleSquare(square));
      demoBoard.append(tile);
    });
  });
}

function canPlaySquare(square) {
  if (gameMode === "ai") return turn === "white" && colorOf(boardState[square]) === "white";
  return turn === onlineColor && colorOf(boardState[square]) === onlineColor;
}

function handleSquare(square) {
  if (gameMode === "ai" && turn !== "white") {
    moveStatus.textContent = "Attends le coup de l'IA.";
    return;
  }
  if (gameMode === "online" && turn !== onlineColor) {
    moveStatus.textContent = "C'est le tour de ton adversaire.";
    return;
  }

  if (!selected) {
    if (canPlaySquare(square) && legalMovesFrom(square).length > 0) {
      selected = square;
      moveStatus.textContent = `Piece selectionnee: ${square}.`;
    }
    buildDemoBoard();
    return;
  }

  const move = { from: selected, to: square };
  if (legalMovesFrom(selected).includes(square)) {
    boardState = applyMove(boardState, move);
    turn = turn === "white" ? "black" : "white";
    selected = null;
    buildDemoBoard();
    if (gameMode === "online") sendOnline({ type: "move", room: currentRoom, move, board: boardState, turn });
    if (gameMode === "ai") {
      moveStatus.textContent = `Tu joues ${move.from}-${move.to}. L'IA calcule...`;
      window.setTimeout(playAiReply, 450);
    } else {
      moveStatus.textContent = `Coup joue ${move.from}-${move.to}.`;
    }
    return;
  }

  selected = null;
  moveStatus.textContent = "Selection annulee.";
  buildDemoBoard();
}

function playAiReply() {
  const moves = allLegalMoves("black");
  if (moves.length === 0) {
    moveStatus.textContent = "L'IA n'a plus de coup disponible.";
    turn = "white";
    return;
  }
  const move = chooseAiMove();
  boardState = applyMove(boardState, move);
  turn = "white";
  moveStatus.textContent = `IA joue ${move.from}-${move.to}. A toi.`;
  buildDemoBoard();
}

function resetDemo(countGame = true) {
  boardState = { ...START_POSITION };
  selected = null;
  turn = "white";
  moveStatus.textContent = gameMode === "online" ? "Partie en ligne prete." : "Selectionne une piece blanche.";
  if (countGame) currentUser.games = (currentUser.games || 0) + 1;
  updateProfile();
  saveCurrentUser();
  buildDemoBoard();
}

function enterGame(user) {
  const avatar = normalizeAvatar(user.avatar);
  currentUser = {
    username: user.username || "Joueur",
    password: user.password || "",
    avatar,
    games: user.games || 0,
    friends: user.friends || [],
  };
  resetDemo();
  showScreen("game");
}

function addChatMessage(author, text) {
  const div = document.createElement("div");
  div.className = "chat-message";
  div.textContent = `${author}: ${text}`;
  chatMessages.append(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function sendOnline(payload) {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(payload));
    return;
  }
  pendingMessages.push(payload);
}

function connectOnlineRoom() {
  if (!location.host) {
    roomStatus.textContent = "Lance le serveur: node web/server.js";
    addChatMessage("Systeme", "Le mode en ligne demande le serveur web local.");
    return;
  }
  currentRoom = roomInput.value.trim() || "adam-room";
  socket = new WebSocket(`${location.protocol === "https:" ? "wss" : "ws"}://${location.host}`);
  roomStatus.textContent = "Connexion...";
  socket.addEventListener("open", () => {
    socket.send(JSON.stringify({ type: "join", room: currentRoom, name: currentUser.username }));
    pendingMessages.splice(0).forEach((payload) => socket.send(JSON.stringify(payload)));
  });
  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "joined") {
      onlineColor = data.color;
      roomStatus.textContent = `Salon ${data.room} | Tu joues ${onlineColor === "white" ? "blanc" : "noir"}`;
      moveStatus.textContent = onlineColor === "white" ? "A toi de commencer." : "Attends le joueur blanc.";
    }
    if (data.type === "move") {
      boardState = data.board;
      turn = data.turn;
      selected = null;
      buildDemoBoard();
      moveStatus.textContent = turn === onlineColor ? "A toi." : "Tour adverse.";
    }
    if (data.type === "chat") addChatMessage(data.name, data.text);
    if (data.type === "system") addChatMessage("Systeme", data.text);
    if (data.type === "invite") {
      inviteNotice.classList.remove("hidden");
      inviteNotice.innerHTML = "";
      const text = document.createElement("span");
      text.textContent = `${data.from} t'invite a jouer dans le salon ${data.room}.`;
      const accept = document.createElement("button");
      accept.type = "button";
      accept.textContent = "Accepter";
      accept.addEventListener("click", () => {
        roomInput.value = data.room;
        currentRoom = data.room;
        inviteNotice.classList.add("hidden");
        connectOnlineRoom();
      });
      inviteNotice.append(text, accept);
      addFriend(data.from);
    }
    if (data.type === "private") {
      addFriend(data.from);
      addPrivateMessage(data.from, data.text);
    }
  });
  socket.addEventListener("close", () => {
    roomStatus.textContent = "Deconnecte";
  });
}

document.querySelector("#startButton").addEventListener("click", () => showScreen("auth"));
document.querySelector("#infoStartButton").addEventListener("click", () => showScreen("auth"));
document.querySelector("#goLoginTop").addEventListener("click", () => showScreen("auth"));
document.querySelector("#backHomeFromAuth").addEventListener("click", showLanding);
document.querySelector("#logoutButton").addEventListener("click", showLanding);
document.querySelector("#scrollDown").addEventListener("click", () => {
  document.querySelector("#infoScreen").scrollIntoView({ behavior: "smooth" });
});

document.querySelectorAll(".mode-control").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".mode-control").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    gameMode = button.dataset.mode;
    onlinePanel.classList.toggle("hidden", gameMode !== "online");
    updateProfile();
    resetDemo(false);
  });
});

document.querySelectorAll(".level-control").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".level-control").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    levelLabel.textContent = button.dataset.level;
    moveStatus.textContent = `Niveau ${button.dataset.level} active.`;
    updateProfile();
  });
});

document.querySelectorAll(".avatar-choice").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".avatar-choice").forEach((item) => item.classList.remove("active"));
    button.classList.add("active");
    selectedAvatar = {
      name: button.dataset.avatarName,
      style: button.dataset.avatarStyle,
      letter: button.dataset.avatarLetter,
    };
  });
});

document.querySelectorAll(".theme-choice").forEach((button) => {
  button.addEventListener("click", () => setTheme(button.dataset.theme));
});

document.querySelector("#joinRoomButton").addEventListener("click", connectOnlineRoom);

addFriendButton.addEventListener("click", () => {
  addFriend(friendInput.value);
  friendInput.value = "";
});

document.querySelector("#privateForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const to = privateTarget.value.trim();
  const text = privateInput.value.trim();
  if (!to || !text) return;
  addFriend(to);
  addPrivateMessage(currentUser.username, text);
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    addPrivateMessage("Systeme", "Rejoins un salon en mode joueur vs joueur pour envoyer le MP en direct.");
    privateInput.value = "";
    return;
  }
  sendOnline({ type: "private", to, from: currentUser.username, text });
  privateInput.value = "";
});

document.querySelector("#chatForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;
  if (gameMode === "online") {
    sendOnline({ type: "chat", room: currentRoom, text, name: playerName.textContent });
  } else {
    addChatMessage(playerName.textContent, text);
  }
  chatInput.value = "";
});

document.querySelectorAll(".auth-tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    const target = tab.dataset.auth;
    document.querySelectorAll(".auth-tab").forEach((item) => item.classList.remove("active"));
    document.querySelectorAll(".auth-form").forEach((form) => form.classList.remove("active"));
    tab.classList.add("active");
    document.querySelector(`#${target}Form`).classList.add("active");
    authMessage.textContent = target === "login" ? "Bienvenue sur Chess AI." : "Cree ton espace joueur.";
  });
});

document.querySelector("#signupForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const user = {
    username: data.get("username"),
    password: data.get("password"),
    avatar: selectedAvatar,
    games: 0,
    friends: [],
  };
  localStorage.setItem("chessAiUser", JSON.stringify(user));
  authMessage.textContent = `Compte cree. Bienvenue ${user.username}.`;
  enterGame(user);
});

document.querySelector("#loginForm").addEventListener("submit", (event) => {
  event.preventDefault();
  const data = new FormData(event.currentTarget);
  const saved = JSON.parse(localStorage.getItem("chessAiUser") || "null");
  if (!saved) {
    authMessage.textContent = "Aucun compte local. Inscris-toi d'abord.";
    return;
  }
  if (saved.username === data.get("username") && saved.password === data.get("password")) enterGame(saved);
  else authMessage.textContent = "Nom utilisateur ou mot de passe incorrect.";
});

resetBoard.addEventListener("click", resetDemo);
buildFloatingBoard();
buildDemoBoard();

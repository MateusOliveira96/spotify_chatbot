from flask import Flask, render_template, request, jsonify
import json
from pathlib import Path

app = Flask(__name__)
DATA_FILE = Path("playlists.json")

def carregar_playlists():
    if DATA_FILE.exists():
        with DATA_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {}

def salvar_playlists(playlists):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(playlists, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

def parse_intent(msg, playlists):
    m = msg.lower().strip()
    m = m.replace("pra mim", "").replace("por favor", "").strip()

    if any(k in m for k in ["criar playlist", "cria playlist", "crie playlist", "nova playlist", "fazer playlist"]):
        name = m
        for k in ["criar playlist", "cria playlist", "crie playlist", "nova playlist", "fazer playlist"]:
            name = name.replace(k, "")
        name = name.strip() or "Nova Playlist"
        return ("create", {"name": name})

    if any(k in m for k in ["adicionar", "coloca", "coloque", "adiciona", "põe"]):
        if "na playlist" in m:
            musica = m.split("na playlist")[0]
            playlist = m.split("na playlist")[1]
            for k in ["adicionar", "coloca", "coloque", "adiciona", "põe"]:
                musica = musica.replace(k, "")
            musica = musica.strip()
            playlist = playlist.strip()
            return ("add", {"track": musica, "playlist": playlist})

    if any(k in m for k in ["buscar", "procurar", "tem", "acha", "ache"]):
        term = m
        for k in ["buscar", "procurar", "tem", "acha", "ache"]:
            term = term.replace(k, "")
        term = term.strip()
        return ("search", {"term": term})

    if any(k in m for k in ["mostrar playlists", "minhas playlists", "listar playlists", "quais playlists"]):
        return ("list_playlists", {})

    if any(k in m for k in ["mostrar musicas", "mostrar músicas", "quais musicas", "listar musicas"]):
        name = m
        for k in ["mostrar musicas", "mostrar músicas", "quais musicas", "listar musicas"]:
            name = name.replace(k, "")
        name = name.strip()
        return ("list_tracks", {"playlist": name})

    return ("unknown", {})

@app.route("/api/message", methods=["POST"])
def process_message():
    data = request.json
    msg = data.get("message", "").strip()
    playlists = carregar_playlists()

    intent, params = parse_intent(msg, playlists)

    if intent == "create":
        name = params["name"]
        if name in playlists:
            return jsonify({"reply": f"A playlist '{name}' já existe."})
        playlists[name] = []
        salvar_playlists(playlists)
        return jsonify({"reply": f"Playlist '{name}' criada com sucesso!"})

    if intent == "add":
        track = params["track"]
        playlist = params["playlist"]
        if playlist not in playlists:
            return jsonify({"reply": f"Playlist '{playlist}' não encontrada."})
        playlists[playlist].append(track)
        salvar_playlists(playlists)
        return jsonify({"reply": f"{track} adicionada à playlist '{playlist}'."})

    if intent == "search":
        term = params["term"].lower()
        found = []
        for pl, mus in playlists.items():
            for m in mus:
                if term in m.lower():
                    found.append(f"{m} (playlist: {pl})")
        if not found:
            return jsonify({"reply": "Nenhuma música encontrada."})
        return jsonify({"reply": "Resultados:\n" + "\n".join(found)})

    if intent == "list_playlists":
        if not playlists:
            return jsonify({"reply": "Você não tem playlists."})
        text = "Suas playlists:\n" + "\n".join([f"- {p} ({len(m)} músicas)" for p, m in playlists.items()])
        return jsonify({"reply": text})

    if intent == "list_tracks":
        playlist = params.get("playlist", "")
        if playlist not in playlists:
            return jsonify({"reply": f"Playlist '{playlist}' não encontrada."})
        if not playlists[playlist]:
            return jsonify({"reply": f"A playlist '{playlist}' está vazia."})
        return jsonify({"reply": "Músicas:\n" + "\n".join(playlists[playlist])})

    return jsonify({"reply": "Desculpe, não entendi. Tente: 'criar playlist rock' ou 'adicionar wisp na playlist rock'" })

if __name__ == '__main__':
    app.run(debug=True)

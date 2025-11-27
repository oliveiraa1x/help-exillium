# amantes.py
"""
Sistema web simples para gerenciar 'amantes' (relacionamentos privados).
Uso educacional: não incentive ou promova condutas danosas.
Dependências:
"""
import datetime
import asyncio
import discord
import sqlite3
import csv
import os
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from functools import wraps
from flask import (
    Flask, g, render_template_string, request, redirect, url_for,
    flash, send_file, abort, Response
)
from cryptography.fernet import Fernet

# ----------------------------
# CONFIGURAÇÃO
# ----------------------------
APP_SECRET = os.environ.get("AMANTES_SECRET") or "troque-esta-chave-por-uma-segura"
DB_PATH = os.environ.get("AMANTES_DB") or "amantes.db"
KEY_PATH = os.environ.get("AMANTES_KEY") or "amantes.key"  # chave para cifrar notas sensíveis

# Geração / carregamento da chave de cifragem
if not os.path.exists(KEY_PATH):
    key = Fernet.generate_key()
    with open(KEY_PATH, "wb") as f:
        f.write(key)
else:
    key = open(KEY_PATH, "rb").read()

fernet = Fernet(key)

app = Flask(__name__)
app.secret_key = APP_SECRET

# ----------------------------
# UTIL / DB
# ----------------------------
def get_db():
    db = getattr(g, "_db", None)
    if db is None:
        db = g._db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def init_db():
    """Cria tabelas iniciais se não existirem"""
    db = get_db()
    with app.open_resource(None, mode='r') as f:  # trick to silence static check
        pass
    # criar tabelas
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,   -- NOTE: senha em texto aqui para simplicidade; troque por hash em produção
        is_admin INTEGER DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        nickname TEXT,
        phone TEXT,
        email TEXT,
        notes_encrypted BLOB,
        created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS relations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        person_a INTEGER NOT NULL,
        person_b INTEGER NOT NULL,
        relation_type TEXT NOT NULL,
        started_at TEXT,
        ended_at TEXT,
        created_at TEXT NOT NULL,
        created_by INTEGER,
        FOREIGN KEY(person_a) REFERENCES people(id),
        FOREIGN KEY(person_b) REFERENCES people(id),
        FOREIGN KEY(created_by) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS meetings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        relation_id INTEGER NOT NULL,
        when_dt TEXT NOT NULL,
        place TEXT,
        notes_encrypted BLOB,
        created_at TEXT NOT NULL,
        created_by INTEGER,
        FOREIGN KEY(relation_id) REFERENCES relations(id),
        FOREIGN KEY(created_by) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ts TEXT NOT NULL,
        user_id INTEGER,
        action TEXT NOT NULL
    );
    """)
    db.commit()

# ----------------------------
# AUTH BÁSICA (simplicada)
# ----------------------------
def current_user():
    uid = request.cookies.get("uid")
    if not uid:
        return None
    user = query_db("SELECT * FROM users WHERE id = ?", (uid,), one=True)
    return user

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user:
            flash("Faça login primeiro.", "warning")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = current_user()
        if not user or not user["is_admin"]:
            abort(403)
        return f(*args, **kwargs)
    return decorated

# ----------------------------
# HELPERS: cifrar / decifrar notas
# ----------------------------
def encrypt_text(plain: str) -> bytes:
    if plain is None:
        return None
    return fernet.encrypt(plain.encode())

def decrypt_text(blob: bytes):
    if not blob:
        return ""
    try:
        return fernet.decrypt(blob).decode()
    except Exception:
        return "[ERRO NA CIPHRA]"

# ----------------------------
# LOG
# ----------------------------
def log_action(user_id, action):
    db = get_db()
    db.execute("INSERT INTO logs (ts, user_id, action) VALUES (?, ?, ?)",
               (datetime.utcnow().isoformat(), user_id, action))
    db.commit()

# ----------------------------
# ROTAS
# ----------------------------
HOME_HTML = """
<!doctype html>
<title>Amantes - Sistema</title>
<h1>Amantes - Sistema</h1>
<p style="color:darkred"><strong>Aviso ético:</strong> Este software é apenas um exemplo técnico. Antes de registrar informações sensíveis sobre outras pessoas,
assegure-se de obter consentimento. O autor não incentiva condutas danosas.</p>
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for cat, msg in messages %}
    <div style="border:1px solid #ccc;padding:8px;margin:6px;background:#f8f8f8">{{ msg }}</div>
  {% endfor %}
{% endwith %}
{% if user %}
  <p>Olá, <strong>{{ user['username'] }}</strong> |
     <a href="{{ url_for('logout') }}">Sair</a></p>
  <ul>
    <li><a href="{{ url_for('list_people') }}">Pessoas</a></li>
    <li><a href="{{ url_for('list_relations') }}">Relações</a></li>
    <li><a href="{{ url_for('search') }}">Pesquisar</a></li>
    {% if user['is_admin'] %}
      <li><a href="{{ url_for('export_csv') }}">Exportar CSV (admin)</a></li>
      <li><a href="{{ url_for('view_logs') }}">Ver Logs</a></li>
    {% endif %}
  </ul>
{% else %}
  <p><a href="{{ url_for('login') }}">Login</a> ou <a href="{{ url_for('register') }}">Registrar conta</a></p>
{% endif %}
"""

@app.route("/")
def home():
    user = current_user()
    return render_template_string(HOME_HTML, user=user)

# ---------- login / logout / register ----------
LOGIN_HTML = """
<!doctype html><title>Login</title>
<h2>Login</h2>
<form method="post">
  Usuário: <input name="username"><br>
  Senha: <input name="password" type="password"><br>
  <button>Entrar</button>
</form>
<p><a href="{{ url_for('register') }}">Criar conta</a></p>
"""

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        user = query_db("SELECT * FROM users WHERE username = ? AND password = ?", (u, p), one=True)
        if user:
            resp = redirect(request.args.get("next") or url_for("home"))
            # cookie simples com uid (simplificado)
            resp.set_cookie("uid", str(user["id"]), httponly=True)
            flash("Login realizado.", "success")
            log_action(user["id"], f"login")
            return resp
        else:
            flash("Usuário/senha inválidos.", "danger")
    return render_template_string(LOGIN_HTML)

@app.route("/logout")
def logout():
    resp = redirect(url_for("home"))
    resp.delete_cookie("uid")
    flash("Desconectado.", "info")
    return resp

REGISTER_HTML = """
<!doctype html><title>Registrar</title>
<h2>Registrar nova conta</h2>
<form method="post">
  Usuário: <input name="username"><br>
  Senha: <input name="password" type="password"><br>
  Código de admin (opcional): <input name="admkey"><br>
  <button>Criar</button>
</form>
"""

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        admkey = request.form.get("admkey", "")
        if not u or not p:
            flash("Preencha usuário e senha.", "warning")
            return redirect(url_for("register"))
        is_admin = 1 if admkey == "ADMIN_SECRET" else 0
        db = get_db()
        try:
            db.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", (u, p, is_admin))
            db.commit()
            flash("Conta criada. Faça login.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Usuário já existe.", "danger")
    return render_template_string(REGISTER_HTML)

# ---------- Pessoas ----------
LIST_PEOPLE_HTML = """
<!doctype html><title>Pessoas</title>
<h2>Pessoas</h2>
<p><a href="{{ url_for('home') }}">Inicio</a> | <a href="{{ url_for('create_person') }}">Nova pessoa</a></p>
<table border=1 cellpadding=6>
<tr><th>ID</th><th>Nome</th><th>Nickname</th><th>Contatos</th><th>Criado_em</th><th>Ações</th></tr>
{% for p in people %}
  <tr>
    <td>{{ p['id'] }}</td>
    <td>{{ p['name'] }}</td>
    <td>{{ p['nickname'] or '' }}</td>
    <td>{{ p['phone'] or '' }}<br>{{ p['email'] or '' }}</td>
    <td>{{ p['created_at'] }}</td>
    <td>
      <a href="{{ url_for('view_person', person_id=p['id']) }}">Ver</a> |
      <a href="{{ url_for('edit_person', person_id=p['id']) }}">Editar</a> |
      <a href="{{ url_for('delete_person', person_id=p['id']) }}">Excluir</a>
    </td>
  </tr>
{% endfor %}
</table>
"""

CREATE_PERSON_HTML = """
<!doctype html><title>Criar pessoa</title>
<h2>Criar pessoa</h2>
<form method="post">
  Nome: <input name="name"><br>
  Nickname: <input name="nickname"><br>
  Telefone: <input name="phone"><br>
  Email: <input name="email"><br>
  Notas (sensíveis, serão cifradas):<br>
  <textarea name="notes" rows=6 cols=60></textarea><br>
  <button>Salvar</button>
</form>
<p><a href="{{ url_for('list_people') }}">Voltar</a></p>
"""

VIEW_PERSON_HTML = """
<!doctype html><title>Ver pessoa</title>
<h2>{{ p['name'] }}</h2>
<p><strong>Nickname:</strong> {{ p['nickname'] }}</p>
<p><strong>Telefone:</strong> {{ p['phone'] }}</p>
<p><strong>Email:</strong> {{ p['email'] }}</p>
<p><strong>Notas:</strong><br><pre>{{ notes }}</pre></p>
<p><a href="{{ url_for('list_people') }}">Voltar</a></p>
"""

@app.route("/people")
@login_required
def list_people():
    rows = query_db("SELECT * FROM people ORDER BY created_at DESC")
    return render_template_string(LIST_PEOPLE_HTML, people=rows)

@app.route("/people/new", methods=["GET", "POST"])
@login_required
def create_person():
    if request.method == "POST":
        name = request.form.get("name")
        nickname = request.form.get("nickname")
        phone = request.form.get("phone")
        email = request.form.get("email")
        notes = request.form.get("notes")
        enc = encrypt_text(notes) if notes else None
        db = get_db()
        db.execute("INSERT INTO people (name, nickname, phone, email, notes_encrypted, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                   (name, nickname, phone, email, enc, datetime.utcnow().isoformat()))
        db.commit()
        user = current_user()
        log_action(user["id"] if user else None, f"create_person:{name}")
        flash("Pessoa criada.", "success")
        return redirect(url_for("list_people"))
    return render_template_string(CREATE_PERSON_HTML)

@app.route("/people/<int:person_id>")
@login_required
def view_person(person_id):
    p = query_db("SELECT * FROM people WHERE id = ?", (person_id,), one=True)
    if not p:
        flash("Pessoa não encontrada.", "danger")
        return redirect(url_for("list_people"))
    notes = decrypt_text(p["notes_encrypted"])
    return render_template_string(VIEW_PERSON_HTML, p=p, notes=notes)

@app.route("/people/<int:person_id>/edit", methods=["GET", "POST"])
@login_required
def edit_person(person_id):
    p = query_db("SELECT * FROM people WHERE id = ?", (person_id,), one=True)
    if not p:
        flash("Pessoa não encontrada.", "danger")
        return redirect(url_for("list_people"))
    if request.method == "POST":
        name = request.form.get("name")
        nickname = request.form.get("nickname")
        phone = request.form.get("phone")
        email = request.form.get("email")
        notes = request.form.get("notes")
        enc = encrypt_text(notes) if notes else None
        db = get_db()
        db.execute("UPDATE people SET name=?, nickname=?, phone=?, email=?, notes_encrypted=? WHERE id=?",
                   (name, nickname, phone, email, enc, person_id))
        db.commit()
        log_action(current_user()["id"], f"edit_person:{person_id}")
        flash("Atualizado.", "success")
        return redirect(url_for("view_person", person_id=person_id))
    # mostrar form preenchido
    notes = decrypt_text(p["notes_encrypted"])
    form = f"""
    <!doctype html><title>Editar</title>
    <h2>Editar {p['name']}</h2>
    <form method="post">
      Nome: <input name="name" value="{p['name']}"><br>
      Nickname: <input name="nickname" value="{p['nickname'] or ''}"><br>
      Telefone: <input name="phone" value="{p['phone'] or ''}"><br>
      Email: <input name="email" value="{p['email'] or ''}"><br>
      Notas (sensíveis):<br>
      <textarea name="notes" rows=6 cols=60>{notes}</textarea><br>
      <button>Salvar</button>
    </form>
    <p><a href="{url_for('view_person', person_id=person_id)}">Voltar</a></p>
    """
    return form

@app.route("/people/<int:person_id>/delete")
@login_required
def delete_person(person_id):
    db = get_db()
    db.execute("DELETE FROM people WHERE id = ?", (person_id,))
    db.commit()
    log_action(current_user()["id"], f"delete_person:{person_id}")
    flash("Pessoa excluída.", "info")
    return redirect(url_for("list_people"))

# ---------- Relações ----------
LIST_REL_HTML = """
<!doctype html><title>Relações</title>
<h2>Relações</h2>
<p><a href="{{ url_for('home') }}">Inicio</a> | <a href="{{ url_for('create_relation') }}">Nova relação</a></p>
<table border=1 cellpadding=6>
<tr><th>ID</th><th>Pessoa A</th><th>Pessoa B</th><th>Tipo</th><th>Início</th><th>Fim</th><th>Ações</th></tr>
{% for r in rels %}
  <tr>
    <td>{{ r['id'] }}</td>
    <td>{{ r['a_name'] }}</td>
    <td>{{ r['b_name'] }}</td>
    <td>{{ r['relation_type'] }}</td>
    <td>{{ r['started_at'] or '' }}</td>
    <td>{{ r['ended_at'] or '' }}</td>
    <td>
      <a href="{{ url_for('view_relation', rel_id=r['id']) }}">Ver</a> |
      <a href="{{ url_for('close_relation', rel_id=r['id']) }}">Encerrar</a>
    </td>
  </tr>
{% endfor %}
</table>
"""

CREATE_REL_HTML = """
<!doctype html><title>Nova relação</title>
<h2>Nova relação</h2>
<form method="post">
  Pessoa A (id): <input name="a"><br>
  Pessoa B (id): <input name="b"><br>
  Tipo (ex: amante, parceiro, ex): <input name="t"><br>
  Data início (YYYY-MM-DD) (opcional): <input name="start"><br>
  <button>Criar</button>
</form>
<p><small>Use a página de Pessoas para ver IDs.</small></p>
"""

VIEW_REL_HTML = """
<!doctype html><title>Ver relação</title>
<h2>Relação #{{ r['id'] }}</h2>
<p><strong>{{ r['a_name'] }}</strong> — {{ r['relation_type'] }} — <strong>{{ r['b_name'] }}</strong></p>
<p>Início: {{ r['started_at'] or 'N/A' }} | Fim: {{ r['ended_at'] or 'N/A' }}</p>
<hr>
<h3>Encontros</h3>
<p><a href="{{ url_for('add_meeting', rel_id=r['id']) }}">Adicionar encontro</a></p>
<table border=1 cellpadding=6>
<tr><th>ID</th><th>Quando</th><th>Local</th><th>Notas</th><th>Ações</th></tr>
{% for m in meetings %}
  <tr>
    <td>{{ m['id'] }}</td>
    <td>{{ m['when_dt'] }}</td>
    <td>{{ m['place'] }}</td>
    <td><pre>{{ m['notes'] }}</pre></td>
    <td><a href="{{ url_for('delete_meeting', meeting_id=m['id'], rel_id=r['id']) }}">Excluir</a></td>
  </tr>
{% endfor %}
</table>
<p><a href="{{ url_for('list_relations') }}">Voltar</a></p>
"""

@app.route("/relations")
@login_required
def list_relations():
    rows = query_db("""
      SELECT r.*, pa.name as a_name, pb.name as b_name
      FROM relations r
      JOIN people pa ON pa.id = r.person_a
      JOIN people pb ON pb.id = r.person_b
      ORDER BY r.created_at DESC
    """)
    return render_template_string(LIST_REL_HTML, rels=rows)

@app.route("/relations/new", methods=["GET", "POST"])
@login_required
def create_relation():
    if request.method == "POST":
        a = int(request.form.get("a"))
        b = int(request.form.get("b"))
        t = request.form.get("t")
        start = request.form.get("start") or None
        db = get_db()
        db.execute("INSERT INTO relations (person_a, person_b, relation_type, started_at, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                   (a, b, t, start, datetime.utcnow().isoformat(), current_user()["id"]))
        db.commit()
        log_action(current_user()["id"], f"create_relation:{a}-{b}:{t}")
        flash("Relação criada.", "success")
        return redirect(url_for("list_relations"))
    return render_template_string(CREATE_REL_HTML)

@app.route("/relations/<int:rel_id>")
@login_required
def view_relation(rel_id):
    r = query_db("SELECT r.*, pa.name as a_name, pb.name as b_name FROM relations r JOIN people pa ON pa.id=r.person_a JOIN people pb ON pb.id=r.person_b WHERE r.id=?", (rel_id,), one=True)
    if not r:
        flash("Relação não encontrada.", "danger")
        return redirect(url_for("list_relations"))
    meetings = query_db("SELECT * FROM meetings WHERE relation_id = ? ORDER BY when_dt DESC", (rel_id,))
    # decrypt notes
    meetings_list = []
    for m in meetings:
        meetings_list.append({
            "id": m["id"],
            "when_dt": m["when_dt"],
            "place": m["place"],
            "notes": decrypt_text(m["notes_encrypted"])
        })
    return render_template_string(VIEW_REL_HTML, r=r, meetings=meetings_list)

@app.route("/relations/<int:rel_id>/close")
@login_required
def close_relation(rel_id):
    db = get_db()
    db.execute("UPDATE relations SET ended_at=? WHERE id=?", (datetime.utcnow().date().isoformat(), rel_id))
    db.commit()
    log_action(current_user()["id"], f"close_relation:{rel_id}")
    flash("Relação encerrada.", "info")
    return redirect(url_for("view_relation", rel_id=rel_id))

# ---------- Encontros / Meetings ----------
ADD_MEETING_HTML = """
<!doctype html><title>Adicionar encontro</title>
<h2>Adicionar encontro para relação {{ rel_id }}</h2>
<form method="post">
  Data e hora (YYYY-MM-DD HH:MM): <input name="when_dt"><br>
  Local: <input name="place"><br>
  Notas (sensíveis):<br>
  <textarea name="notes" rows=6 cols=60></textarea><br>
  <button>Salvar encontro</button>
</form>
"""

@app.route("/relations/<int:rel_id>/meetings/new", methods=["GET", "POST"])
@login_required
def add_meeting(rel_id):
    rel = query_db("SELECT * FROM relations WHERE id = ?", (rel_id,), one=True)
    if not rel:
        flash("Relação não encontrada.", "danger")
        return redirect(url_for("list_relations"))
    if request.method == "POST":
        when_dt = request.form.get("when_dt")
        place = request.form.get("place")
        notes = request.form.get("notes")
        enc = encrypt_text(notes) if notes else None
        db = get_db()
        db.execute("INSERT INTO meetings (relation_id, when_dt, place, notes_encrypted, created_at, created_by) VALUES (?, ?, ?, ?, ?, ?)",
                   (rel_id, when_dt, place, enc, datetime.utcnow().isoformat(), current_user()["id"]))
        db.commit()
        log_action(current_user()["id"], f"add_meeting:rel{rel_id}")
        flash("Encontro adicionado.", "success")
        return redirect(url_for("view_relation", rel_id=rel_id))
    return render_template_string(ADD_MEETING_HTML, rel_id=rel_id)

@app.route("/relations/<int:rel_id>/meetings/<int:meeting_id>/delete")
@login_required
def delete_meeting(rel_id, meeting_id):
    db = get_db()
    db.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
    db.commit()
    log_action(current_user()["id"], f"delete_meeting:{meeting_id}")
    flash("Encontro excluído.", "info")
    return redirect(url_for("view_relation", rel_id=rel_id))

# ---------- Busca ----------
SEARCH_HTML = """
<!doctype html><title>Pesquisar</title>
<h2>Pesquisar pessoas / relações</h2>
<form method="get" action="{{ url_for('search') }}">
  Query: <input name="q" value="{{ q or '' }}"> <button>Pesquisar</button>
</form>
{% if people or relations %}
<h3>Resultados</h3>
{% if people %}
  <h4>Pessoas</h4>
  <ul>{% for p in people %}<li><a href="{{ url_for('view_person', person_id=p['id']) }}">{{ p['name'] }}</a></li>{% endfor %}</ul>
{% endif %}
{% if relations %}
  <h4>Relações</h4>
  <ul>{% for r in relations %}<li><a href="{{ url_for('view_relation', rel_id=r['id']) }}">{{ r['a_name'] }} - {{ r['relation_type'] }} - {{ r['b_name'] }}</a></li>{% endfor %}</ul>
{% endif %}
{% endif %}
"""

@app.route("/search")
@login_required
def search():
    q = request.args.get("q", "").strip()
    people = []
    relations = []
    if q:
        like = f"%{q}%"
        people = query_db("SELECT * FROM people WHERE name LIKE ? OR nickname LIKE ?", (like, like))
        relations = query_db("""
            SELECT r.*, pa.name as a_name, pb.name as b_name
            FROM relations r
            JOIN people pa ON pa.id=r.person_a
            JOIN people pb ON pb.id=r.person_b
            WHERE pa.name LIKE ? OR pb.name LIKE ? OR relation_type LIKE ?
        """, (like, like, like))
    return render_template_string(SEARCH_HTML, q=q, people=people, relations=relations)

# ---------- Export / Logs (admin) ----------
@app.route("/export")
@admin_required
def export_csv():
    # Export pessoas, relações, encontros (NOTAS cifradas não são exportadas decifradas por segurança)
    db = get_db()
    people = query_db("SELECT * FROM people")
    relations = query_db("SELECT * FROM relations")
    meetings = query_db("SELECT * FROM meetings")
    def generate():
        w = csv.writer(Response(stream_with_context=False))
        # header
        w.writerow(["people_id","name","nickname","phone","email","created_at"])
        for p in people:
            w.writerow([p["id"], p["name"], p["nickname"], p["phone"], p["email"], p["created_at"]])
        w.writerow([])
        w.writerow(["relations_id","person_a","person_b","type","started_at","ended_at","created_at","created_by"])
        for r in relations:
            w.writerow([r["id"], r["person_a"], r["person_b"], r["relation_type"], r["started_at"], r["ended_at"], r["created_at"], r["created_by"]])
        w.writerow([])
        w.writerow(["meetings_id","relation_id","when_dt","place","created_at","created_by"])
        for m in meetings:
            w.writerow([m["id"], m["relation_id"], m["when_dt"], m["place"], m["created_at"], m["created_by"]])
    # Simpler: create a temp CSV file and send it
    fname = f"export_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
    with open(fname, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["PEOPLE"])
        w.writerow(["id","name","nickname","phone","email","created_at"])
        for p in people:
            w.writerow([p["id"], p["name"], p["nickname"], p["phone"], p["email"], p["created_at"]])
        w.writerow([])
        w.writerow(["RELATIONS"])
        w.writerow(["id","person_a","person_b","type","started_at","ended_at","created_at","created_by"])
        for r in relations:
            w.writerow([r["id"], r["person_a"], r["person_b"], r["relation_type"], r["started_at"], r["ended_at"], r["created_at"], r["created_by"]])
        w.writerow([])
        w.writerow(["MEETINGS"])
        w.writerow(["id","relation_id","when_dt","place","created_at","created_by"])
        for m in meetings:
            w.writerow([m["id"], m["relation_id"], m["when_dt"], m["place"], m["created_at"], m["created_by"]])
    return send_file(fname, as_attachment=True)

@app.route("/logs")
@admin_required
def view_logs():
    logs = query_db("SELECT l.*, u.username as user FROM logs l LEFT JOIN users u ON u.id = l.user_id ORDER BY l.ts DESC LIMIT 500")
    html = "<h2>Logs</h2><p><a href='/'>Inicio</a></p><table border=1 cellpadding=6><tr><th>ts</th><th>user</th><th>action</th></tr>"
    for lg in logs:
        html += f"<tr><td>{lg['ts']}</td><td>{lg['user'] or 'anon'}</td><td>{lg['action']}</td></tr>"
    html += "</table>"
    return html

# ----------------------------
# HOOKS
# ----------------------------
@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "_db", None)
    if db is not None:
        db.close()

# ----------------------------
# UTILIDADES / Ajustes inicias
# ----------------------------
def bootstrap():
    # cria DB se necessário e cria um usuário admin por default (senha: admin)
    if not os.path.exists(DB_PATH):
        print("Inicializando banco...")
    with app.app_context():
        init_db()
        # criar admin se não existir
        admin = query_db("SELECT * FROM users WHERE username = ?", ("admin",), one=True)
        if not admin:
            db = get_db()
            db.execute("INSERT INTO users (username, password, is_admin) VALUES (?, ?, ?)", ("admin", "admin", 1))
            db.commit()
            print("Usuário admin criado: user=admin pass=admin (Mude a senha!)")

if __name__ == "__main__":
    bootstrap()
    app.run(debug=True, host="0.0.0.0", port=5000)

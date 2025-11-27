# gf.py testando banco de dados simples de pessoas e relacionamentos

import json
import os
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from uuid import uuid4

# ==============================
# arquivos
# ==============================

ARQ_PESSOAS = "pessoas.json"
ARQ_RELACOES = "relacoes.json"
ARQ_LOGS = "logs.txt"

# ==============================
# util
# ==============================

def carregar(arquivo):
    if not os.path.exists(arquivo):
        return []
    with open(arquivo, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def log(msg):
    with open(ARQ_LOGS, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# ==============================
# pessoas
# ==============================

def cadastrar_pessoa():

    print("\n=== CADASTRO ===\n")

    nome = input("Nome completo: ").strip()
    idade = input("Idade: ").strip()
    sexo = input("Sexo: ").strip()
    cidade = input("Cidade: ").strip()

    if nome == "":
        print("Erro: nome inválido.")
        return

    nova = {
        "id": uuid4().hex[:8],
        "nome": nome,
        "idade": idade,
        "sexo": sexo,
        "cidade": cidade
    }

    lista = carregar(ARQ_PESSOAS)
    lista.append(nova)
    salvar(ARQ_PESSOAS, lista)

    print("\nPessoa cadastrada com sucesso!\n")
    log(f"Nova pessoa cadastrada: {nome}")


def listar_pessoas():

    lista = carregar(ARQ_PESSOAS)

    if not lista:
        print("\nNenhuma pessoa cadastrada.\n")
        return

    print("\n=== PESSOAS ===\n")

    for p in lista:
        print(f"- {p['id']} | {p['nome']} | {p['cidade']}")

    print()


# ==============================
# relacionamento
# ==============================

ListaTipos = [
    "casado",
    "namorada",
    "namorado",
    "amante",
    "ficante",
    "relacionamento aberto",
    "contratual"
]

def registrar_relacao():

    print("\n=== REGISTRAR RELAÇÃO ===\n")

    pessoas = carregar(ARQ_PESSOAS)

    if len(pessoas) < 2:
        print("ERRO: menos de duas pessoas cadastradas.")
        return

    print("\nDigite o ID das pessoas envolvidas:\n")

    id1 = input("Pessoa 1: ").strip()
    id2 = input("Pessoa 2: ").strip()

    tipo = input(f"Tipo ({','.join(ListaTipos)}): ").strip().lower()

    if tipo not in ListaTipos:
        print("Tipo inválido.")
        return

    data = datetime.now().strftime("%d/%m/%Y %H:%M")

    nova = {
        "id": uuid4().hex[:12],
        "p1": id1,
        "p2": id2,
        "tipo": tipo,
        "data": data
    }

    rels = carregar(ARQ_RELACOES)
    rels.append(nova)
    salvar(ARQ_RELACOES, rels)

    print("\nRelacionamento registrado!\n")
    log(f"Relacionamento registrado: {id1}+{id2} [{tipo}]")


def listar_relacoes():

    rels = carregar(ARQ_RELACOES)
    pessoas = carregar(ARQ_PESSOAS)

    dic = {x["id"]: x["nome"] for x in pessoas}

    if not rels:
        print("\nNenhum relacionamento registrado.\n")
        return

    print("\n=== RELAÇÕES ===\n")

    for r in rels:
        n1 = dic.get(r['p1'], "???")
        n2 = dic.get(r['p2'], "???")
        print(f"[{r['tipo']}] {n1}  +  {n2}    ({r['data']})")

    print()


# ==============================
# relatório
# ==============================

def relatorio():

    pessoas = carregar(ARQ_PESSOAS)
    rels = carregar(ARQ_RELACOES)

    print("\n===== RELATÓRIO GLOBAL =====")

    print(f"Pessoas cadastradas: {len(pessoas)}")
    print(f"Relacionamentos: {len(rels)}")

    t = {}

    for r in rels:
        t.setdefault(r["tipo"], 0)
        t[r["tipo"]] += 1

    print("\nPor categoria:\n")

    for i, v in t.items():
        print(f"- {i}: {v}")

    print("\n============================\n")


# ==============================
# menu
# ==============================

def menu():
    while True:
        print("""
=====================
 SISTEMA GF MASTER
=====================

1 - Cadastrar pessoa
2 - Listar pessoas

3 - Registrar relacionamento
4 - Listar relacionamentos

5 - Relatório geral

0 - Sair
""")

        op = input("Opção: ").strip()

        if op == "1":
            cadastrar_pessoa()
        elif op == "2":
            listar_pessoas()
        elif op == "3":
            registrar_relacao()
        elif op == "4":
            listar_relacoes()
        elif op == "5":
            relatorio()
        elif op == "0":
            break
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()
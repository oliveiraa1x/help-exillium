# 🤖 Help Exilium Bot

Bot Discord completo para **Aeternum Exilium** com sistema de economia, níveis, perfil e muito mais!

---

## ✨ Funcionalidades

- 💰 **Sistema de Economia** - Moeda (Souls), níveis e XP
- 📊 **Rankings** - Top players em diferentes categorias
- 🎯 **Missões** - Complete missões e ganhe recompensas
- 🎧 **Tracking de Call** - Acompanhe tempo em chamadas de voz
- ⛏️ **Mineração** - Mine recursos e ganhe souls
- 🌲 **Sistema de Caça** - Caça rápida e caça longa por almas

---

## 🚀 Instalação Rápida

1. **Instale as dependências:**

```bash
pip install -r requirements.txt
```

2. **Configure o token:**

   - Crie um arquivo `.env` com: `TOKEN=seu_token_aqui`
   - Ou crie `config.json` com: `{"TOKEN": "seu_token_aqui"}`

3. **Execute:**

```bash
python main.py
```

---

## 📝 Comandos Principais

### 💰 Economia

| Comando             | Descrição                             | Cooldown |
| ------------------- | ------------------------------------- | -------- |
| `/daily`            | Recompensa diária (50-150 souls + XP) | 24h      |
| `/mine`             | Minerar e ganhar souls (10-50 souls)  | 60s      |
| `/caça`             | Caça rápida (15-60 souls)             | 2min     |
| `/caça-longa`       | Caça longa de 12h (200-500 souls)     | 12h      |
| `/balance [membro]` | Ver saldo de souls e XP               | -        |
| `/top-souls`        | Ranking de souls                      | -        |
| `/top-level`        | Ranking de níveis                     | -        |

### 👤 Perfil

| Comando              | Descrição                            |
| -------------------- | ------------------------------------ |
| `/perfil [membro]`   | Perfil completo com stats e rankings |
| `/set-sobre <texto>` | Definir seu "Sobre Mim"              |

### 🎯 Missões

| Comando                  | Descrição                    |
| ------------------------ | ---------------------------- |
| `/missoes`               | Ver missões ativas           |
| `/claim-missao <número>` | Reivindicar recompensa (1-3) |

### 🎧 Call

| Comando       | Descrição                |
| ------------- | ------------------------ |
| `/callstatus` | Tempo atual em call      |
| `/top-tempo`  | Ranking de tempo em call |

### 🔧 Utilitários

| Comando                      | Descrição                 |
| ---------------------------- | ------------------------- |
| `/help`                      | Lista todos os comandos   |
| `/mensagem <título> <texto>` | Criar embed personalizada |
| `/uptime`                    | Tempo online do bot       |

---

## 💎 Sistema de Economia

### Moeda: Souls

Ganhe souls através de:

- ✅ Daily rewards
- ⛏️ Mineração
- 🌲 Caça (rápida e longa)
- 🎯 Missões completas

### Sistema de Níveis

Ganhe **XP** enviando mensagens, fazendo daily, minerando, caçando ou completando missões.

**Fórmula:** XP necessária aumenta 50% a cada nível

### Recompensas

**Daily:**

- 50-150 souls + 20-50 XP
- Bônus de streak (+10% por dia)

**Mineração:**

- 10-50 souls + 5-15 XP
- Chance de itens raros (5-10%)

**Caça Rápida:**

- 15-60 souls + 8-20 XP
- Duração: 5 segundos
- Chance de almas raras (4-8%)

**Caça Longa:**

- 200-500 souls + 100-250 XP
- Duração: 12 horas
- Notificação automática ao terminar
- Maiores chances de itens raros (15-20%)

---

## 🎯 Tipos de Missões

| Tipo        | Objetivo            | Recompensa       |
| ----------- | ------------------- | ---------------- |
| Daily       | Coletar daily       | 25 souls + 15 XP |
| Mineração   | Minerar 5 vezes     | 50 souls + 30 XP |
| Comunicador | Enviar 20 mensagens | 40 souls + 25 XP |
| Social      | 30min em call       | 60 souls + 40 XP |

---

## 📁 Estrutura

```
help-exillium/
├── main.py              # Bot principal
├── cogs/                # Módulos
│   ├── economia.py      # Sistema de economia
│   ├── perfil.py        # Sistema de perfil
│   └── ...
└── data/db.json         # Banco de dados
```

---

## 🛠️ Tecnologias

- **Python 3.10+**
- **discord.py 2.3.2**
- **python-dotenv 1.0.1**

---

## 📊 Rankings

O perfil mostra automaticamente seu ranking em:

- 🏆 **Top Call** - Tempo total em call
- 💎 **Top Souls** - Quantidade de souls
- ⭐ **Top XP** - Experiência total

---

## 📝 Notas

- Bot precisa de permissões adequadas no servidor
- Banco de dados criado automaticamente
- XP ganha automaticamente ao enviar mensagens (cooldown: 30s)

---

**Desenvolvido para Aeternum Exilium** 🎮

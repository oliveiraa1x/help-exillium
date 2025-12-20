# 🤖 Help Exilium Bot

Bot Discord completo para **Aeternum Exilium** com sistema de economia, níveis, perfil e muito mais!

---

## ✨ Funcionalidades

- 💰 **Sistema de Economia** - Moeda (Almas), níveis e XP
- 📊 **Rankings** - Top players em diferentes categorias
- 🎯 **Missões** - Complete missões e ganhe recompensas
- 🎧 **Tracking de Call** - Acompanhe tempo em chamadas de voz
- ⛏️ **Mineração** - Mine recursos e ganhe almas
- 🌲 **Sistema de Caça** - Caça rápida e caça longa por almas
- 🏪 **Loja Completa** - Compre items consumíveis, lootboxes e especiais
- ⚒️ **Sistema de Forja** - Crie armas lendárias com risco de falha
- 🔨 **Crafting** - Combine materiais para criar novos items
- 📦 **Inventário** - Gerencie seus items e equipáveis
- 🏪 **Mercado** - Compre e venda items entre players

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
| `/daily`            | Recompensa diária (50-150 almas + XP) | 24h      |
| `/mine`             | Minerar e ganhar almas (10-50 almas)  | 60s      |
| `/caça`             | Caça rápida (15-60 almas)             | 2min     |
| `/caça-longa`       | Caça longa de 12h (200-500 almas)     | 12h      |
| `/balance [membro]` | Ver saldo de almas e XP               | -        |
| `/top-souls`        | Ranking de almas                      | -        |

### 🏪 Loja & Inventário

| Comando      | Descrição                                  | Tipo   |
| ------------ | ------------------------------------------ | ------ |
| `/loja`      | Abra a loja (consumíveis, caixas, extras)  | Buyer  |
| `/comprar`   | Compre items com almas                     | Buyer  |
| `/vender`    | Venda items (recebe 70% do valor)          | Seller |
| `/inventario`| Veja seus items e almas                    | View   |

### ⚒️ Crafting & Forja

| Comando | Descrição                                  | Tipo      |
| ------- | ------------------------------------------ | --------- |
| `/craft`| Crafta items usando materiais              | Crafting  |
| `/forjar` | Forja armas lendárias (com risco 12-25%) | Crafting  |
| `/ranking` | Top 10 jogadores mais ricos            | Leaderboard |

---

## 🛒 Sistema de Loja

### Itens Disponíveis (34 total)

**Craft** (9 itens)
- Lingote Etéreo, Núcleo Purificado, Runas Reforçadas, Cristal Lapidado, Amuleto Incompleto, Pergaminho Rasgado, Essência Concentrada, Selo Místico, Fragmento Encantado

**Forja** (6 armas)
- Lâmina do Exílio, Punhal das Almas, Martelo do Vazio, Orbe da Eternidade, Totem Espiritual, Coração Arcano

**Passivos** (4 equipáveis)
- Amuleto da Sorte (+15% drops), Anel da Ganância (2x almas), Talismã do Silêncio (-20% dano), Colar da Persistência (+25% regen)

**Consumíveis** (6 itens)
- Poção de Alma, Elixir da Fortuna (+50% almas/1h), Incenso Espiritual (+30% drops), Fragmento da Sorte, Pergaminho de Bênção, Essência Restauradora

**Lootboxes** (4 caixas)
- Caixa Comum, Caixa Rara, Caixa Ancestral, Caixa do Vazio

**Especiais** (5 itens raros)
- Alma Corrompida, Fragmento do Exilium, Relíquia Perdida, Selo do Criador, Essência Primordial

### Raridades & Multiplicadores
- ⚪ Comum: 1.0x
- 🔵 Raro: 2.5x
- 🟣 Épico: 5.0x
- 🟡 Lendário: 10.0x
- 🔴 Ancestral: 20.0x

### Economia Balanceada
- ✅ Taxa de falha na forja (12-25%) - Remove almas
- ✅ Venda com penalidade (70% retorno) - Previne flip
- ✅ Custo duplo (almas + materiais) - Risco real
- ✅ Sem farm infinito - Progresso controlado
| `/top-level`        | Ranking de níveis                     | -        |

| `/pay @membro valor` | Enviar almas para outro membro (requer confirmação do destinatário) | - |

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

### 🔧 Moderação

| Comando                                  | Descrição                                         | Permissão    |
| ---------------------------------------- | ------------------------------------------------- | ------------ |
| `sprt!painel`                            | Painel interativo de moderação (botões)           | -            |
| `sprt!tempo [@membro]`                   | Mostra tempo em call do membro (ou autor)         | -            |
| `sprt!addcargo @membro @cargo [tempo]`   | Adiciona cargo; remove após duração (s/m/h/d)     | Manage Roles |
| `sprt!removercargo @membro @cargo`       | Remove cargo do membro                            | Manage Roles |
| `sprt!criarcargo @membro NomeDoCargo`    | Cria cargo (se não existir) e adiciona ao membro  | Manage Roles |
| `sprt!deletecargo @membro @cargo\|Nome`  | Remove cargo; se ficar vazio, deleta o cargo      | Manage Roles |
| `sprt!mutecall @membro [tempo] [motivo]` | Muta membro em voice (opcional: tempo automático) | Mute Members |
| `sprt!unmutecall @membro`                | Desmuta membro em voice                           | Mute Members |
| `sprt!prender @membro [tempo] [motivo]`  | Move para canal 'Prisão' e muta/deafen            | Move Members |
| `sprt!soltar @membro`                    | Desmuta/deaf do membro e libera                   | Move Members |
| `sprt!ban @membro [motivo]`              | Bane permanentemente o membro                     | Ban Members  |
| `sprt!unban <user_id> [motivo]`          | Remove ban pelo ID do usuário                     | Ban Members  |
| `sprt!help`                              | Lista comandos de moderação (requer Manage Guild) | Manage Guild |

**Painel de Moderação (`sprt!painel`):**

- ⚠️ **Advertência** - Modal para aplicar advertência
- 🔇 **Mute** - Modal para mutar com duração (10m, 2h, 1d)
- 👢 **Kick** - Modal para expulsar membro
- 🔨 **Ban** - Modal para banir membro

**MuteModal:**

- Modal independente para aplicar mute com duração em minutos
- Aceita ID ou menção do membro
- Registra punições em arquivo JSON

### 🔧 Utilitários

| Comando                      | Descrição                 |
| ---------------------------- | ------------------------- |
| `/help`                      | Lista todos os comandos   |
| `/mensagem <título> <texto>` | Criar embed personalizada |
| `/uptime`                    | Tempo online do bot       |

---

## 💎 Sistema de Economia

### Moeda: Almas

Ganhe almas através de:

- ✅ Daily rewards
- ⛏️ Mineração
- 🌲 Caça (rápida e longa)
- 🎯 Missões completas

### Sistema de Níveis

Ganhe **XP** enviando mensagens, fazendo daily, minerando, caçando ou completando missões.

**Fórmula:** XP necessária aumenta 50% a cada nível

### Recompensas

**Daily:**

- 50-150 almas + 20-50 XP
- Bônus de streak (+10% por dia)

**Mineração:**

- 10-50 almas + 5-15 XP
- Chance de itens raros (5-10%)

**Caça Rápida:**

- 15-60 almas + 8-20 XP
- Duração: 5 segundos
- Chance de almas raras (4-8%)

**Caça Longa:**

- 200-500 almas + 100-250 XP
- Duração: 12 horas
- Notificação automática ao terminar
- Maiores chances de itens raros (15-20%)

---

## 🎯 Tipos de Missões

| Tipo        | Objetivo            | Recompensa       |
| ----------- | ------------------- | ---------------- |
| Daily       | Coletar daily       | 25 almas + 15 XP |
| Mineração   | Minerar 5 vezes     | 50 almas + 30 XP |
| Comunicador | Enviar 20 mensagens | 40 almas + 25 XP |
| Social      | 30min em call       | 60 almas + 40 XP |

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
- 💎 **Top Almas** - Quantidade de almas
- ⭐ **Top XP** - Experiência total

---

## 📝 Notas

- Bot precisa de permissões adequadas no servidor
- Banco de dados criado automaticamente
- XP ganha automaticamente ao enviar mensagens (cooldown: 30s)

---

## 🆕 Novidades / Alterações Recentes

- `/pay @membro valor`: novo comando para enviar almas para outro membro. O envio só é concluído quando o destinatário confirma a transferência clicando no botão de confirmação enviado na mensagem. Isso evita envios não autorizados e permite revalidação de saldo no momento da confirmação.
- Persistência de tempo em call: corrigimos a inicialização das estruturas em memória e garantimos que o tempo total em call seja salvo em `data/top_tempo.json` quando usuários saem da call. Usuários novos agora têm registro criado automaticamente no banco de economia (`data/economia.json`) para que missões relacionadas à call sejam atualizadas corretamente.
- Revalidação de saldo no `/pay`: o saldo do remetente é rechecado no momento em que o destinatário confirma, evitando condições de corrida.

-- Testes rápidos:

1. Reinicie o bot:
```powershell
python main.py
```
2. Entre/saia de uma call para verificar que `data/top_tempo.json` é atualizado.
3. Use `/pay @Usuario 100` e peça para o destinatário confirmar clicando no botão; verifique `data/economia.json` para ver débito/crédito.

Se quiser, posso adicionar persistência de transferências pendentes (para sobreviver a reinícios antes da confirmação) ou um botão de cancelar para o remetente.

---

**Desenvolvido para Aeternum Exilium** 🎮

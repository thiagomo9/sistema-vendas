import sqlite3
import os
import sys
import customtkinter as ctk
from datetime import datetime

def obter_diretorio_base():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

DIRETORIO_BASE = obter_diretorio_base()
DB_PATH = os.path.join(DIRETORIO_BASE, 'sistema_vendas.db')

def conectar():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;") 
    return conn

def aplicar_configuracoes_globais():
    try:
        conn = conectar()
        conf = conn.execute("SELECT tema, escala FROM configuracoes WHERE id=1").fetchone()
        conn.close()
        
        if conf:
            ctk.set_appearance_mode(conf[0])
            escala_float = float(conf[1].replace("%", "")) / 100
            ctk.set_widget_scaling(escala_float)
            ctk.set_window_scaling(escala_float)
    except Exception:
        ctk.set_appearance_mode("Dark")
        ctk.set_widget_scaling(1.2)

def registrar_log(usuario, acao):
    try:
        conn = conectar()
        data_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn.execute("INSERT INTO logs (data_hora, usuario, acao) VALUES (?, ?, ?)", (data_agora, usuario, acao))
        conn.commit()
        conn.close()
    except Exception:
        pass

def verificar_permissao(cargo, recurso):
    if cargo in ["Desenvolvedor", "Admin"]:
        return True
        
    try:
        conn = conectar()
        res = conn.execute("SELECT permitido FROM permissoes WHERE cargo=? AND recurso=?", (cargo, recurso)).fetchone()
        conn.close()
        
        if res:
            return bool(res[0])
        else:
            return False
    except Exception:
        return False

def configurar_banco():
    conn = conectar()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT, 
            preco REAL, 
            estoque INTEGER, 
            preco_custo REAL DEFAULT 0.0,
            cod_barras TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT, 
            cpf TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            cliente_id INTEGER, 
            vendedor_id INTEGER DEFAULT 1, 
            valor_total REAL, 
            data_hora TEXT, 
            forma_pagto TEXT, 
            status TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS itens_venda (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            venda_id INTEGER, 
            produto_id INTEGER,
            nome_produto TEXT, 
            preco REAL, 
            quantidade INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            username TEXT UNIQUE, 
            password TEXT, 
            role TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresa (
            id INTEGER PRIMARY KEY, 
            nome TEXT, 
            cnpj TEXT, 
            endereco TEXT, 
            telefone TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracoes (
            id INTEGER PRIMARY KEY, 
            tema TEXT, 
            escala TEXT, 
            ultimo_backup TEXT DEFAULT 'Nunca realizado',
            nome_sistema TEXT DEFAULT 'MASTER PRO',
            ver_vendedores INTEGER DEFAULT 1,
            ver_contas_pagar INTEGER DEFAULT 1,
            ver_dados_empresa INTEGER DEFAULT 1,
            ver_usuarios INTEGER DEFAULT 1,
            ver_permissoes INTEGER DEFAULT 1,
            ver_auditoria INTEGER DEFAULT 1,
            auto_backup INTEGER DEFAULT 1,
            descanso_tela INTEGER DEFAULT 0,
            tempo_descanso INTEGER DEFAULT 5,
            ver_orcamentos INTEGER DEFAULT 1,
            ver_num_pedido INTEGER DEFAULT 1,
            ver_cod_barras INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parcelas (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            venda_id INTEGER, 
            numero_parcela INTEGER, 
            valor REAL, 
            data_vencimento TEXT, 
            data_pagamento TEXT, 
            status TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contas_pagar (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            descricao TEXT, 
            valor REAL, 
            data_vencimento TEXT, 
            data_pagamento TEXT, 
            status TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licenca (
            id INTEGER PRIMARY KEY, 
            hwid TEXT, 
            chave TEXT, 
            data_expiracao TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT, 
            telefone TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS formas_pagto (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT UNIQUE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            data_hora TEXT, 
            usuario TEXT, 
            acao TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissoes (
            cargo TEXT, 
            recurso TEXT, 
            permitido INTEGER, 
            UNIQUE(cargo, recurso)
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM configuracoes")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO configuracoes 
            (id, tema, escala, nome_sistema, auto_backup, descanso_tela, tempo_descanso, ver_orcamentos, ver_num_pedido, ver_cod_barras) 
            VALUES (1, 'Dark', '120%', 'MASTER PRO', 1, 0, 5, 1, 1, 1)
        """)

    cursor.execute("SELECT COUNT(*) FROM empresa")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO empresa (id, nome, cnpj, endereco, telefone) 
            VALUES (1, 'SUA EMPRESA', 'CNPJ', 'Endereço', 'Telefone')
        """)

    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO usuarios (username, password, role) 
            VALUES ('dev', 'admin', 'Desenvolvedor')
        """)

    cursor.execute("SELECT COUNT(*) FROM formas_pagto")
    if cursor.fetchone()[0] == 0:
        formas_iniciais = ['Dinheiro', 'Pix', 'Cartão', 'A Prazo']
        for pag in formas_iniciais:
            cursor.execute("INSERT OR IGNORE INTO formas_pagto (nome) VALUES (?)", (pag,))

    cursor.execute("SELECT COUNT(*) FROM vendedores")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO vendedores (id, nome, telefone) 
            VALUES (1, 'Vendedor Padrão', '0000000000')
        """)

    recursos = [
        'menu_vendas', 'menu_cadastros', 'menu_financeiro', 'menu_historico', 
        'aba_receber', 'aba_pagar', 'aba_editar_vendas', 'aba_relatorios'
    ]
    for r in recursos:
        cursor.execute("INSERT OR IGNORE INTO permissoes (cargo, recurso, permitido) VALUES ('Gerente', ?, 1)", (r,))
        perm_caixa = 1 if r in ['menu_vendas', 'menu_historico'] else 0
        cursor.execute("INSERT OR IGNORE INTO permissoes (cargo, recurso, permitido) VALUES ('Caixa', ?, ?)", (r, perm_caixa))

    # Migrações Silenciosas
    colunas_config = [
        "ver_dados_empresa", "ver_usuarios", "ver_permissoes", "ver_auditoria", 
        "auto_backup", "descanso_tela", "tempo_descanso", "ver_orcamentos", "ver_num_pedido", "ver_cod_barras"
    ]
    for col in colunas_config:
        try: cursor.execute(f"ALTER TABLE configuracoes ADD COLUMN {col} INTEGER DEFAULT 1")
        except: pass
            
    try: cursor.execute("ALTER TABLE produtos ADD COLUMN preco_custo REAL DEFAULT 0.0")
    except: pass
    try: cursor.execute("ALTER TABLE produtos ADD COLUMN cod_barras TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE itens_venda ADD COLUMN produto_id INTEGER")
    except: pass
    try: cursor.execute("ALTER TABLE itens_venda ADD COLUMN quantidade INTEGER DEFAULT 1")
    except: pass

    conn.commit()
    conn.close()

configurar_banco()
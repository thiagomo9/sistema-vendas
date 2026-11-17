import customtkinter as ctk
import sqlite3
from tkinter import messagebox
from database import conectar, registrar_log

def setup_cadastros(container, usuario_logado, cargo_usuario):
    tabview = ctk.CTkTabview(container)
    tabview.pack(fill="both", expand=True)
    
    conn = conectar()
    try:
        perm = conn.execute("SELECT ver_vendedores FROM configuracoes WHERE id=1").fetchone()
        liberar_vendedores = perm[0] if perm else 1
    except:
        liberar_vendedores = 1
    conn.close()

    tabview.add("📦 Produtos")
    tabview.add("👥 Clientes")
    
    if liberar_vendedores == 1 or cargo_usuario == "Desenvolvedor":
        tabview.add("👔 Vendedores")
    
    if cargo_usuario == "Desenvolvedor":
        tabview.add("💳 Formas de Pagto")

    render_aba_produtos(tabview.tab("📦 Produtos"), usuario_logado)
    render_aba_clientes(tabview.tab("👥 Clientes"), usuario_logado)
    
    if liberar_vendedores == 1 or cargo_usuario == "Desenvolvedor":
        render_aba_vendedores(tabview.tab("👔 Vendedores"), usuario_logado)
        
    if cargo_usuario == "Desenvolvedor":
        render_aba_formas_pagto(tabview.tab("💳 Formas de Pagto"), usuario_logado)


# =========================================================
# 1. ABA: PRODUTOS (OTIMIZAÇÃO EXTREMA LIMIT 20)
# =========================================================
def render_aba_produtos(tab, usuario_logado):
    conn = conectar()
    try:
        conf = conn.execute("SELECT ver_cod_barras FROM configuracoes WHERE id=1").fetchone()
        liberar_barras = conf[0] if conf else 1
    except:
        liberar_barras = 1
    conn.close()

    f_master = ctk.CTkFrame(tab, fg_color="transparent")
    f_master.pack(fill="x", padx=10, pady=10)
    
    lbl_modo = ctk.CTkLabel(f_master, text="NOVO CADASTRO DE PRODUTO", font=("Arial", 18, "bold"), text_color="#3498db")
    lbl_modo.pack(pady=(0, 15))
    
    # --- LINHA 1 ---
    f_linha1 = ctk.CTkFrame(f_master, fg_color="transparent")
    f_linha1.pack(fill="x", padx=20, pady=5)
    
    bloco_id = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_id.pack(side="left", padx=10)
    ctk.CTkLabel(bloco_id, text="ID (Auto):", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_id = ctk.CTkEntry(bloco_id, width=80, state="readonly", fg_color="#2c3e50")
    ent_id.pack(fill="x")
    
    bloco_nome = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_nome.pack(side="left", fill="x", expand=True, padx=10)
    ctk.CTkLabel(bloco_nome, text="Nome Completo do Produto:", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_nome = ctk.CTkEntry(bloco_nome)
    ent_nome.pack(fill="x")

    # --- LINHA 2 ---
    f_linha2 = ctk.CTkFrame(f_master, fg_color="transparent")
    f_linha2.pack(fill="x", padx=20, pady=5)
    
    ent_barras = None
    if liberar_barras == 1:
        bloco_barras = ctk.CTkFrame(f_linha2, fg_color="transparent")
        bloco_barras.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(bloco_barras, text="CÓD DE BARRAS:", font=("Arial", 12, "bold"), text_color="#e74c3c").pack(anchor="w")
        ent_barras = ctk.CTkEntry(bloco_barras, placeholder_text="Opcional...")
        ent_barras.pack(fill="x")
    
    bloco_custo = ctk.CTkFrame(f_linha2, fg_color="transparent")
    bloco_custo.pack(side="left", padx=10, fill="x", expand=True)
    ctk.CTkLabel(bloco_custo, text="Preço de Custo (R$):", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_custo = ctk.CTkEntry(bloco_custo)
    ent_custo.pack(fill="x")
    
    bloco_venda = ctk.CTkFrame(f_linha2, fg_color="transparent")
    bloco_venda.pack(side="left", padx=10, fill="x", expand=True)
    ctk.CTkLabel(bloco_venda, text="Preço de Venda (R$):", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_preco = ctk.CTkEntry(bloco_venda)
    ent_preco.pack(fill="x")
    
    bloco_est = ctk.CTkFrame(f_linha2, fg_color="transparent")
    bloco_est.pack(side="left", padx=10, fill="x", expand=True)
    ctk.CTkLabel(bloco_est, text="Qtd Estoque:", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_estoque = ctk.CTkEntry(bloco_est)
    ent_estoque.pack(fill="x")

    # --- BOTÕES DE AÇÃO ---
    f_btns = ctk.CTkFrame(f_master, fg_color="transparent")
    f_btns.pack(pady=20)
    
    btn_salvar = ctk.CTkButton(f_btns, text="💾 GRAVAR DADOS", fg_color="green", hover_color="#27ae60", height=40)
    btn_salvar.pack(side="left", padx=10)
    
    btn_cancelar = ctk.CTkButton(f_btns, text="✖ CANCELAR EDIÇÃO", fg_color="#c0392b", hover_color="#e74c3c", height=40)

    ctk.CTkFrame(tab, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=10)
    
    f_busca = ctk.CTkFrame(tab, fg_color="transparent")
    f_busca.pack(fill="x", padx=20, pady=5)
    
    lbl_busca = "🔍 Buscar (Nome, ID ou Cód. Barras):" if liberar_barras == 1 else "🔍 Buscar (Nome ou ID):"
    ctk.CTkLabel(f_busca, text=lbl_busca, font=("Arial", 12, "bold")).pack(side="left", padx=5)
    ent_busca_prod = ctk.CTkEntry(f_busca, placeholder_text="Digite para filtrar a lista...", width=350)
    ent_busca_prod.pack(side="left", padx=5, fill="x", expand=True)
    
    btn_atualizar = ctk.CTkButton(f_busca, text="🔄 ATUALIZAR LISTA", fg_color="#3498db", hover_color="#2980b9", width=150)
    btn_atualizar.pack(side="left", padx=10)
    
    frame_lista = ctk.CTkScrollableFrame(tab, fg_color="#1e1e1e")
    frame_lista.pack(fill="both", expand=True, padx=20, pady=10)

    def atualizar_lista(*args):
        for w in frame_lista.winfo_children(): w.destroy()
            
        termo = ent_busca_prod.get().strip()
        conn = conectar()
        try:
            # OTIMIZAÇÃO: LIMIT 20 para fluidez máxima
            query = "SELECT id, nome, preco, estoque, preco_custo, cod_barras FROM produtos WHERE nome LIKE ? OR id LIKE ? OR cod_barras LIKE ? ORDER BY nome ASC LIMIT 20"
            data = conn.execute(query, (f"%{termo}%", f"%{termo}%", f"%{termo}%")).fetchall()
        except:
            query = "SELECT id, nome, preco, estoque, preco_custo FROM produtos WHERE nome LIKE ? OR id LIKE ? ORDER BY nome ASC LIMIT 20"
            data = conn.execute(query, (f"%{termo}%", f"%{termo}%")).fetchall()
        conn.close()
        
        for p in data:
            item = ctk.CTkFrame(frame_lista)
            item.pack(fill="x", pady=2)
            
            ctk.CTkLabel(item, text=f"ID: {p[0]}", width=60).pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"{p[1]}", width=200, anchor="w").pack(side="left", padx=5)
            
            barras_str = p[5] if len(p) > 5 and p[5] else "S/Cód"
            if liberar_barras == 1:
                ctk.CTkLabel(item, text=f"Cód: {barras_str}", width=120, text_color="gray").pack(side="left", padx=5)
            
            custo_val = float(p[4] if p[4] is not None else 0.0)
            ctk.CTkLabel(item, text=f"Custo: R$ {custo_val:.2f}", width=120, text_color="#e74c3c").pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"Venda: R$ {p[2]:.2f}", width=120, text_color="#2ecc71").pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"Estoque: {p[3]}", width=80).pack(side="left", padx=5)
            
            btn_editar = ctk.CTkButton(item, text="✏️ EDITAR", width=80, fg_color="#f39c12", text_color="black", command=lambda prod=p: carregar(prod))
            btn_editar.pack(side="right", padx=5)
            
        # AVISO CASO O LIMITE DE 20 SEJA ATINGIDO
        if len(data) == 20:
            ctk.CTkLabel(frame_lista, text="⚠️ Mostrando apenas os 20 primeiros resultados. Use a pesquisa para encontrar itens específicos.", text_color="#f39c12", font=("Arial", 11, "italic")).pack(pady=10)

    def carregar(p):
        ent_id.configure(state="normal")
        ent_id.delete(0, 'end')
        ent_id.insert(0, p[0])
        ent_id.configure(state="readonly")
        
        ent_nome.delete(0, 'end')
        ent_nome.insert(0, p[1])
        
        ent_preco.delete(0, 'end')
        ent_preco.insert(0, f"{p[2]:.2f}")
        
        ent_estoque.delete(0, 'end')
        ent_estoque.insert(0, p[3])
        
        ent_custo.delete(0, 'end')
        custo_val = float(p[4] if p[4] is not None else 0.0)
        ent_custo.insert(0, f"{custo_val:.2f}")
        
        if ent_barras is not None:
            ent_barras.delete(0, 'end')
            if len(p) > 5 and p[5]: ent_barras.insert(0, p[5])
        
        lbl_modo.configure(text="📝 MODO DE EDIÇÃO ATIVO", text_color="#f39c12")
        btn_cancelar.pack(side="left", padx=10)
        ent_nome.focus()

    def cancelar_edicao():
        ent_id.configure(state="normal")
        ent_id.delete(0, 'end')
        ent_id.configure(state="readonly")
        
        ent_nome.delete(0, 'end')
        ent_preco.delete(0, 'end')
        ent_custo.delete(0, 'end')
        ent_estoque.delete(0, 'end')
        if ent_barras is not None: ent_barras.delete(0, 'end')
        
        lbl_modo.configure(text="NOVO CADASTRO DE PRODUTO", text_color="#3498db")
        btn_cancelar.pack_forget()

    def salvar():
        nome = ent_nome.get().strip()
        preco_str = ent_preco.get().replace(",", ".")
        custo_str = ent_custo.get().replace(",", ".")
        est_str = ent_estoque.get().strip()
        barras = ent_barras.get().strip() if ent_barras is not None else ""
        
        if not nome or not preco_str:
            messagebox.showerror("Erro", "O Nome e o Preço de Venda são obrigatórios.")
            return
            
        try:
            preco = float(preco_str)
            custo = float(custo_str) if custo_str else 0.0
            est = int(est_str) if est_str else 0
        except ValueError:
            messagebox.showerror("Erro", "Certifique-se de que os preços e o estoque são números válidos.")
            return

        conn = conectar()
        is_update = bool(ent_id.get())
        
        if is_update:
            pid = ent_id.get()
            try:
                conn.execute("UPDATE produtos SET nome=?, preco=?, estoque=?, preco_custo=?, cod_barras=? WHERE id=?", (nome, preco, est, custo, barras, pid))
            except:
                conn.execute("UPDATE produtos SET nome=?, preco=?, estoque=?, preco_custo=? WHERE id=?", (nome, preco, est, custo, pid))
        else:
            try:
                conn.execute("INSERT INTO produtos (nome, preco, estoque, preco_custo, cod_barras) VALUES (?,?,?,?,?)", (nome, preco, est, custo, barras))
            except:
                conn.execute("INSERT INTO produtos (nome, preco, estoque, preco_custo) VALUES (?,?,?,?)", (nome, preco, est, custo))
            
        conn.commit()
        conn.close()
        
        if is_update:
            registrar_log(usuario_logado, f"Editou o Produto #{pid} ({nome}) - Venda: R${preco:.2f}, Est: {est}")
            messagebox.showinfo("Sucesso", "Produto atualizado com sucesso!")
        else:
            registrar_log(usuario_logado, f"Cadastrou o Produto '{nome}' - Venda: R${preco:.2f}, Est: {est}")
            messagebox.showinfo("Sucesso", "Novo produto cadastrado com sucesso!")
        
        cancelar_edicao()
        atualizar_lista()

    btn_salvar.configure(command=salvar)
    btn_cancelar.configure(command=cancelar_edicao)
    btn_atualizar.configure(command=atualizar_lista)
    
    ent_busca_prod.bind("<KeyRelease>", atualizar_lista)
    ent_busca_prod.bind("<FocusIn>", lambda e: atualizar_lista())
    atualizar_lista()


# =========================================================
# 2. ABA: CLIENTES (OTIMIZAÇÃO EXTREMA LIMIT 20)
# =========================================================
def render_aba_clientes(tab, usuario_logado):
    f_master = ctk.CTkFrame(tab, fg_color="transparent")
    f_master.pack(fill="x", padx=10, pady=10)
    
    lbl_modo = ctk.CTkLabel(f_master, text="NOVO CADASTRO DE CLIENTE", font=("Arial", 18, "bold"), text_color="#3498db")
    lbl_modo.pack(pady=(0, 15))
    
    f_linha1 = ctk.CTkFrame(f_master, fg_color="transparent")
    f_linha1.pack(fill="x", padx=20, pady=5)

    bloco_id = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_id.pack(side="left", padx=10)
    ctk.CTkLabel(bloco_id, text="ID (Auto):", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_id = ctk.CTkEntry(bloco_id, width=80, state="readonly", fg_color="#2c3e50")
    ent_id.pack(fill="x")

    bloco_nome = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_nome.pack(side="left", fill="x", expand=True, padx=10)
    ctk.CTkLabel(bloco_nome, text="Nome Completo do Cliente:", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_nome = ctk.CTkEntry(bloco_nome)
    ent_nome.pack(fill="x")

    bloco_cpf = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_cpf.pack(side="left", fill="x", expand=True, padx=10)
    ctk.CTkLabel(bloco_cpf, text="CPF / CNPJ:", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_cpf = ctk.CTkEntry(bloco_cpf)
    ent_cpf.pack(fill="x")

    f_btns = ctk.CTkFrame(f_master, fg_color="transparent")
    f_btns.pack(pady=20)
    
    btn_salvar = ctk.CTkButton(f_btns, text="💾 GRAVAR DADOS", fg_color="green", hover_color="#27ae60", height=40)
    btn_salvar.pack(side="left", padx=10)
    
    btn_cancelar = ctk.CTkButton(f_btns, text="✖ CANCELAR EDIÇÃO", fg_color="#c0392b", hover_color="#e74c3c", height=40)

    ctk.CTkFrame(tab, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=10)
    
    f_busca = ctk.CTkFrame(tab, fg_color="transparent")
    f_busca.pack(fill="x", padx=20, pady=5)
    
    ctk.CTkLabel(f_busca, text="🔍 Buscar Cliente:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
    ent_busca_cli = ctk.CTkEntry(f_busca, placeholder_text="Digite o nome do cliente...", width=350)
    ent_busca_cli.pack(side="left", padx=5, fill="x", expand=True)
    
    btn_atualizar = ctk.CTkButton(f_busca, text="🔄 ATUALIZAR LISTA", fg_color="#3498db", hover_color="#2980b9", width=150)
    btn_atualizar.pack(side="left", padx=10)
    
    frame_lista = ctk.CTkScrollableFrame(tab, fg_color="#1e1e1e")
    frame_lista.pack(fill="both", expand=True, padx=20, pady=10)

    def atualizar_lista(*args):
        for w in frame_lista.winfo_children():
            w.destroy()
            
        termo = ent_busca_cli.get().strip()
        conn = conectar()
        # OTIMIZAÇÃO: LIMIT 20 para evitar travamentos de interface
        query = "SELECT id, nome, cpf FROM clientes WHERE nome LIKE ? ORDER BY nome ASC LIMIT 20"
        data = conn.execute(query, (f"%{termo}%",)).fetchall()
        conn.close()
        
        for c in data:
            item = ctk.CTkFrame(frame_lista)
            item.pack(fill="x", pady=2)
            
            ctk.CTkLabel(item, text=f"ID: {c[0]}", width=60).pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"{c[1]}", width=300, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"Documento: {c[2]}", width=200).pack(side="left", padx=5)
            
            btn_editar = ctk.CTkButton(item, text="✏️ EDITAR", width=80, fg_color="#f39c12", text_color="black", command=lambda cli=c: carregar(cli))
            btn_editar.pack(side="right", padx=5)
            
        if len(data) == 20:
            ctk.CTkLabel(frame_lista, text="⚠️ Mostrando apenas os 20 primeiros resultados. Use a pesquisa para encontrar itens específicos.", text_color="#f39c12", font=("Arial", 11, "italic")).pack(pady=10)

    def carregar(c):
        ent_id.configure(state="normal")
        ent_id.delete(0, 'end')
        ent_id.insert(0, c[0])
        ent_id.configure(state="readonly")
        ent_nome.delete(0, 'end')
        ent_nome.insert(0, c[1])
        ent_cpf.delete(0, 'end')
        ent_cpf.insert(0, c[2])
        
        lbl_modo.configure(text="📝 MODO DE EDIÇÃO ATIVO", text_color="#f39c12")
        btn_cancelar.pack(side="left", padx=10)
        ent_nome.focus()

    def cancelar_edicao():
        ent_id.configure(state="normal")
        ent_id.delete(0, 'end')
        ent_id.configure(state="readonly")
        ent_nome.delete(0, 'end')
        ent_cpf.delete(0, 'end')
        lbl_modo.configure(text="NOVO CADASTRO DE CLIENTE", text_color="#3498db")
        btn_cancelar.pack_forget()

    def salvar():
        nome = ent_nome.get().strip()
        cpf = ent_cpf.get().strip()
        if not nome:
            messagebox.showerror("Erro", "O nome do cliente é obrigatório.")
            return

        conn = conectar()
        is_update = bool(ent_id.get())
        if is_update:
            cid = ent_id.get()
            conn.execute("UPDATE clientes SET nome=?, cpf=? WHERE id=?", (nome, cpf, cid))
        else:
            conn.execute("INSERT INTO clientes (nome, cpf) VALUES (?,?)", (nome, cpf))
            
        conn.commit()
        conn.close()
        
        if is_update:
            registrar_log(usuario_logado, f"Editou o Cliente #{cid} (Nome: {nome}, Doc: {cpf})")
            messagebox.showinfo("Sucesso", "Cliente atualizado com sucesso!")
        else:
            registrar_log(usuario_logado, f"Cadastrou o Cliente '{nome}'")
            messagebox.showinfo("Sucesso", "Novo cliente cadastrado com sucesso!")
            
        cancelar_edicao()
        atualizar_lista()

    btn_salvar.configure(command=salvar)
    btn_cancelar.configure(command=cancelar_edicao)
    btn_atualizar.configure(command=atualizar_lista)
    
    ent_busca_cli.bind("<KeyRelease>", atualizar_lista)
    ent_busca_cli.bind("<FocusIn>", lambda e: atualizar_lista())
    atualizar_lista()


# =========================================================
# 3. ABA: VENDEDORES
# =========================================================
def render_aba_vendedores(tab, usuario_logado):
    f_master = ctk.CTkFrame(tab, fg_color="transparent")
    f_master.pack(fill="x", padx=10, pady=10)
    
    lbl_modo = ctk.CTkLabel(f_master, text="NOVO CADASTRO DE VENDEDOR", font=("Arial", 18, "bold"), text_color="#3498db")
    lbl_modo.pack(pady=(0, 15))
    
    f_linha1 = ctk.CTkFrame(f_master, fg_color="transparent")
    f_linha1.pack(fill="x", padx=20, pady=5)

    bloco_id = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_id.pack(side="left", padx=10)
    ctk.CTkLabel(bloco_id, text="ID (Auto):", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_id = ctk.CTkEntry(bloco_id, width=80, state="readonly", fg_color="#2c3e50")
    ent_id.pack(fill="x")

    bloco_nome = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_nome.pack(side="left", fill="x", expand=True, padx=10)
    ctk.CTkLabel(bloco_nome, text="Nome do Vendedor:", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_nome = ctk.CTkEntry(bloco_nome)
    ent_nome.pack(fill="x")

    bloco_tel = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_tel.pack(side="left", fill="x", expand=True, padx=10)
    ctk.CTkLabel(bloco_tel, text="Telefone de Contato:", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_tel = ctk.CTkEntry(bloco_tel)
    ent_tel.pack(fill="x")
    
    f_btns = ctk.CTkFrame(f_master, fg_color="transparent")
    f_btns.pack(pady=20)
    
    btn_salvar = ctk.CTkButton(f_btns, text="💾 GRAVAR DADOS", fg_color="green", hover_color="#27ae60", height=40)
    btn_salvar.pack(side="left", padx=10)
    
    btn_cancelar = ctk.CTkButton(f_btns, text="✖ CANCELAR EDIÇÃO", fg_color="#c0392b", hover_color="#e74c3c", height=40)

    ctk.CTkFrame(tab, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=10)
    
    btn_atualizar = ctk.CTkButton(tab, text="🔄 ATUALIZAR LISTA", fg_color="#3498db", hover_color="#2980b9", width=150)
    btn_atualizar.pack(anchor="w", padx=30, pady=5)
    
    frame_lista = ctk.CTkScrollableFrame(tab, fg_color="#1e1e1e")
    frame_lista.pack(fill="both", expand=True, padx=20, pady=10)

    def atualizar_lista():
        for w in frame_lista.winfo_children():
            w.destroy()
            
        conn = conectar()
        data = conn.execute("SELECT id, nome, telefone FROM vendedores ORDER BY nome ASC").fetchall()
        conn.close()
        
        for v in data:
            item = ctk.CTkFrame(frame_lista)
            item.pack(fill="x", pady=2)
            ctk.CTkLabel(item, text=f"ID: {v[0]}", width=60).pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"{v[1]}", width=300, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"Telefone: {v[2]}", width=200).pack(side="left", padx=5)
            
            if v[0] != 1:
                btn_editar = ctk.CTkButton(item, text="✏️ EDITAR", width=80, fg_color="#f39c12", text_color="black", command=lambda vend=v: carregar(vend))
                btn_editar.pack(side="right", padx=5)
            else:
                ctk.CTkLabel(item, text="(Sistema)", text_color="gray").pack(side="right", padx=15)

    def carregar(v):
        ent_id.configure(state="normal")
        ent_id.delete(0, 'end')
        ent_id.insert(0, v[0])
        ent_id.configure(state="readonly")
        ent_nome.delete(0, 'end')
        ent_nome.insert(0, v[1])
        ent_tel.delete(0, 'end')
        ent_tel.insert(0, v[2])
        
        lbl_modo.configure(text="📝 MODO DE EDIÇÃO ATIVO", text_color="#f39c12")
        btn_cancelar.pack(side="left", padx=10)
        ent_nome.focus()

    def cancelar_edicao():
        ent_id.configure(state="normal")
        ent_id.delete(0, 'end')
        ent_id.configure(state="readonly")
        ent_nome.delete(0, 'end')
        ent_tel.delete(0, 'end')
        lbl_modo.configure(text="NOVO CADASTRO DE VENDEDOR", text_color="#3498db")
        btn_cancelar.pack_forget()

    def salvar():
        nome = ent_nome.get().strip()
        tel = ent_tel.get().strip()
        if not nome:
            messagebox.showerror("Erro", "O nome do vendedor é obrigatório.")
            return

        conn = conectar()
        is_update = bool(ent_id.get())
        if is_update:
            vid = ent_id.get()
            conn.execute("UPDATE vendedores SET nome=?, telefone=? WHERE id=?", (nome, tel, vid))
        else:
            conn.execute("INSERT INTO vendedores (nome, telefone) VALUES (?,?)", (nome, tel))
            
        conn.commit()
        conn.close()
        
        if is_update:
            registrar_log(usuario_logado, f"Editou o Vendedor #{vid} ({nome})")
            messagebox.showinfo("Sucesso", "Vendedor atualizado com sucesso!")
        else:
            registrar_log(usuario_logado, f"Cadastrou o Vendedor '{nome}'")
            messagebox.showinfo("Sucesso", "Novo vendedor cadastrado!")
            
        cancelar_edicao()
        atualizar_lista()

    btn_salvar.configure(command=salvar)
    btn_cancelar.configure(command=cancelar_edicao)
    btn_atualizar.configure(command=atualizar_lista)
    atualizar_lista()


# =========================================================
# 4. ABA: FORMAS DE PAGAMENTO
# =========================================================
def render_aba_formas_pagto(tab, usuario_logado):
    f_master = ctk.CTkFrame(tab, fg_color="transparent")
    f_master.pack(fill="x", padx=10, pady=10)
    
    lbl_modo = ctk.CTkLabel(f_master, text="NOVA FORMA DE PAGAMENTO", font=("Arial", 18, "bold"), text_color="#3498db")
    lbl_modo.pack(pady=(0, 15))
    
    f_linha1 = ctk.CTkFrame(f_master, fg_color="transparent")
    f_linha1.pack(fill="x", padx=20, pady=5)

    bloco_id = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_id.pack(side="left", padx=10)
    ctk.CTkLabel(bloco_id, text="ID (Auto):", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_id = ctk.CTkEntry(bloco_id, width=80, state="readonly", fg_color="#2c3e50")
    ent_id.pack(fill="x")

    bloco_nome = ctk.CTkFrame(f_linha1, fg_color="transparent")
    bloco_nome.pack(side="left", fill="x", expand=True, padx=10)
    ctk.CTkLabel(bloco_nome, text="Nome da Forma de Pagamento:", font=("Arial", 12, "bold")).pack(anchor="w")
    ent_nome = ctk.CTkEntry(bloco_nome)
    ent_nome.pack(fill="x")

    f_btns = ctk.CTkFrame(f_master, fg_color="transparent")
    f_btns.pack(pady=20)
    
    btn_salvar = ctk.CTkButton(f_btns, text="💾 GRAVAR DADOS", fg_color="green", hover_color="#27ae60", height=40)
    btn_salvar.pack(side="left", padx=10)
    
    btn_cancelar = ctk.CTkButton(f_btns, text="✖ CANCELAR EDIÇÃO", fg_color="#c0392b", hover_color="#e74c3c", height=40)

    ctk.CTkFrame(tab, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=10)
    
    btn_atualizar = ctk.CTkButton(tab, text="🔄 ATUALIZAR LISTA", fg_color="#3498db", hover_color="#2980b9", width=150)
    btn_atualizar.pack(anchor="w", padx=30, pady=5)
    
    frame_lista = ctk.CTkScrollableFrame(tab, fg_color="#1e1e1e")
    frame_lista.pack(fill="both", expand=True, padx=20, pady=10)

    formas_protegidas = ['Dinheiro', 'Pix', 'Cartão', 'A Prazo']

    def atualizar_lista():
        for w in frame_lista.winfo_children():
            w.destroy()
            
        conn = conectar()
        data = conn.execute("SELECT id, nome FROM formas_pagto ORDER BY id ASC").fetchall()
        conn.close()
        
        for p in data:
            item = ctk.CTkFrame(frame_lista)
            item.pack(fill="x", pady=2)
            
            ctk.CTkLabel(item, text=f"ID: {p[0]}", width=60).pack(side="left", padx=5)
            ctk.CTkLabel(item, text=f"{p[1]}", width=300, anchor="w").pack(side="left", padx=5)
            
            if p[1] not in formas_protegidas:
                btn_apagar = ctk.CTkButton(item, text="❌ APAGAR", width=80, fg_color="#c0392b", hover_color="#e74c3c", command=lambda f_id=p[0], f_nome=p[1]: apagar(f_id, f_nome))
                btn_apagar.pack(side="right", padx=5)
                
                btn_editar = ctk.CTkButton(item, text="✏️ EDITAR", width=80, fg_color="#f39c12", text_color="black", command=lambda fp=p: carregar(fp))
                btn_editar.pack(side="right", padx=5)
            else:
                ctk.CTkLabel(item, text="(Padrão do Sistema)", text_color="gray").pack(side="right", padx=15)

    def carregar(fp):
        ent_id.configure(state="normal")
        ent_id.delete(0, 'end')
        ent_id.insert(0, fp[0])
        ent_id.configure(state="readonly")
        ent_nome.delete(0, 'end')
        ent_nome.insert(0, fp[1])
        
        lbl_modo.configure(text="📝 MODO DE EDIÇÃO ATIVO", text_color="#f39c12")
        btn_cancelar.pack(side="left", padx=10)
        ent_nome.focus()

    def cancelar_edicao():
        ent_id.configure(state="normal")
        ent_id.delete(0, 'end')
        ent_id.configure(state="readonly")
        ent_nome.delete(0, 'end')
        
        lbl_modo.configure(text="NOVA FORMA DE PAGAMENTO", text_color="#3498db")
        btn_cancelar.pack_forget()

    def salvar():
        nome = ent_nome.get().strip()
        if not nome:
            messagebox.showerror("Erro", "O nome é obrigatório.")
            return

        conn = conectar()
        is_update = bool(ent_id.get())
        try:
            if is_update:
                fid = ent_id.get()
                conn.execute("UPDATE formas_pagto SET nome=? WHERE id=?", (nome, fid))
            else:
                conn.execute("INSERT INTO formas_pagto (nome) VALUES (?)", (nome,))
            conn.commit()
            conn.close()
            
            if is_update:
                registrar_log(usuario_logado, f"Editou a Forma de Pagamento #{fid} para '{nome}'")
                messagebox.showinfo("Sucesso", "Forma de pagamento atualizada!")
            else:
                registrar_log(usuario_logado, f"Cadastrou a Forma de Pagamento '{nome}'")
                messagebox.showinfo("Sucesso", "Forma de pagamento cadastrada!")
        except sqlite3.IntegrityError:
            conn.close()
            messagebox.showerror("Erro", "Esta forma de pagamento já existe no sistema.")
            
        cancelar_edicao()
        atualizar_lista()

    def apagar(f_id, f_nome):
        if messagebox.askyesno("Cuidado", f"Tem certeza que deseja apagar a forma de pagamento '{f_nome}'?"):
            conn = conectar()
            conn.execute("DELETE FROM formas_pagto WHERE id=?", (f_id,))
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, f"Excluiu a Forma de Pagamento '{f_nome}'")
            atualizar_lista()

    btn_salvar.configure(command=salvar)
    btn_cancelar.configure(command=cancelar_edicao)
    btn_atualizar.configure(command=atualizar_lista)
    atualizar_lista()
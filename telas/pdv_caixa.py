import customtkinter as ctk
import sqlite3
from datetime import datetime, timedelta
from tkinter import messagebox

from database import conectar, registrar_log

def setup_vendas(aba, usuario_logado, cargo_usuario):
    estado = {
        "carrinho": [],
        "subtotal": 0.0
    }

    conn = conectar()
    try:
        conf = conn.execute("SELECT ver_vendedores, ver_orcamentos, ver_num_pedido FROM configuracoes WHERE id=1").fetchone()
        liberar_vendedores = conf[0] if conf else 1
        liberar_orcamentos = conf[1] if conf else 1
        liberar_num_pedido = conf[2] if conf else 1
    except:
        liberar_vendedores, liberar_orcamentos, liberar_num_pedido = 1, 1, 1
        
    vendedores_db = conn.execute("SELECT id, nome FROM vendedores ORDER BY nome ASC").fetchall()
    
    max_id = conn.execute("SELECT MAX(id) FROM vendas").fetchone()[0]
    conn.close()
    
    proximo_pedido_id = (max_id or 0) + 1

    # =======================================================
    # INTERFACE DO CAIXA (TOP)
    # =======================================================
    f_cli = ctk.CTkFrame(aba, fg_color="transparent")
    f_cli.pack(fill="x", padx=10, pady=10)
    
    ctk.CTkLabel(f_cli, text="1. Cliente:", font=("Arial", 12, "bold")).pack(side="left", padx=(5, 5))
    ent_busca_cli = ctk.CTkEntry(f_cli, placeholder_text="Buscar Cliente...", width=150)
    ent_busca_cli.pack(side="left", padx=5)
    
    cb_cliente = ctk.CTkComboBox(f_cli, values=["0 - Consumidor"], width=200)
    cb_cliente.pack(side="left", padx=10)

    cb_vendedor = None
    if liberar_vendedores == 1 or cargo_usuario == "Desenvolvedor":
        ctk.CTkLabel(f_cli, text="Vendedor:", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 5))
        lista_vends = [f"{v[0]} - {v[1]}" for v in vendedores_db] if vendedores_db else ["1 - Vendedor Padrão"]
        cb_vendedor = ctk.CTkComboBox(f_cli, values=lista_vends, width=200)
        cb_vendedor.pack(side="left", padx=5)
        for v_str in lista_vends:
            if v_str.startswith("1 -"):
                cb_vendedor.set(v_str)
                break
                
    if liberar_num_pedido == 1:
        lbl_num_pedido = ctk.CTkLabel(f_cli, text=f"PRÓXIMO PEDIDO: #{proximo_pedido_id}", font=("Arial", 14, "bold"), text_color="#f39c12")
        lbl_num_pedido.pack(side="right", padx=20)

    # =======================================================
    # INTERFACE DO CAIXA (MEIO)
    # =======================================================
    f_in = ctk.CTkFrame(aba, fg_color="transparent")
    f_in.pack(fill="x", padx=10, pady=5)
    
    ctk.CTkLabel(f_in, text="2. Produto:", font=("Arial", 12, "bold")).pack(side="left", padx=(5, 5))
    ent_busca_prod = ctk.CTkEntry(f_in, placeholder_text="Buscar Prod, ID ou Cód Barras...", width=250)
    ent_busca_prod.pack(side="left", padx=5)
    
    cb_produto = ctk.CTkComboBox(f_in, values=["Selecione um produto"], width=280)
    cb_produto.pack(side="left", padx=5)
    
    ctk.CTkLabel(f_in, text="Qtd:", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 2))
    ent_qtd = ctk.CTkEntry(f_in, width=45)
    ent_qtd.pack(side="left", padx=(0, 5))
    ent_qtd.insert(0, "1")
    
    ent_preco_alt = ctk.CTkEntry(f_in, placeholder_text="Preço Alt.", width=80)
    ent_preco_alt.pack(side="left", padx=5)
    
    btn_add = ctk.CTkButton(f_in, text="ADD PRODUTO", fg_color="green", hover_color="#27ae60", width=120)
    btn_add.pack(side="left", padx=10)

    frame_lista_caixa = ctk.CTkScrollableFrame(aba, fg_color="#1e1e1e")
    frame_lista_caixa.pack(fill="both", expand=True, padx=10, pady=10)

    # =======================================================
    # INTERFACE DO CAIXA (RODAPÉ)
    # =======================================================
    f_fim = ctk.CTkFrame(aba, fg_color="transparent")
    f_fim.pack(fill="x", padx=10, pady=10)
    
    conn = conectar()
    try:
        formas_db = conn.execute("SELECT nome FROM formas_pagto").fetchall()
        lista_pagamentos = [f[0] for f in formas_db]
    except:
        lista_pagamentos = ["Dinheiro", "Pix", "Cartão", "A Prazo"]
    conn.close()
    
    ctk.CTkLabel(f_fim, text="Pagamento:", font=("Arial", 12, "bold")).pack(side="left", padx=5)
    cb_pagto = ctk.CTkComboBox(f_fim, values=lista_pagamentos, width=120)
    cb_pagto.pack(side="left", padx=5)
    
    ctk.CTkLabel(f_fim, text="Parcelas:", font=("Arial", 12, "bold")).pack(side="left", padx=(10, 2))
    cb_parcelas = ctk.CTkComboBox(f_fim, values=["1x", "2x", "3x", "4x", "5x", "6x", "10x", "12x"], width=70)
    cb_parcelas.pack(side="left", padx=5)

    ctk.CTkLabel(f_fim, text="Desc. Global R$:", font=("Arial", 12, "bold")).pack(side="left", padx=(15, 5))
    ent_desc = ctk.CTkEntry(f_fim, width=80)
    ent_desc.pack(side="left", padx=5)
    ent_desc.insert(0, "0")
    
    lbl_tot = ctk.CTkLabel(f_fim, text="TOTAL: R$ 0,00", font=("Arial", 36, "bold"), text_color="#2ecc71")
    lbl_tot.pack(side="right", padx=20)
    
    f_btns = ctk.CTkFrame(aba, fg_color="transparent")
    f_btns.pack(pady=10)
    
    btn_finalizar = ctk.CTkButton(f_btns, text="FINALIZAR VENDA", height=50, width=300, font=("Arial", 16, "bold"), fg_color="green", hover_color="#27ae60")
    btn_finalizar.pack(side="left", padx=10)

    if liberar_orcamentos == 1:
        btn_orcamento = ctk.CTkButton(f_btns, text="GERAR ORÇAMENTO (NÃO FATURAR)", height=50, width=300, font=("Arial", 14, "bold"), fg_color="#f39c12", text_color="black", hover_color="#e67e22")
        btn_orcamento.pack(side="left", padx=10)

    # =======================================================
    # LÓGICA E FUNÇÕES DO CAIXA
    # =======================================================
    def atualizar_numero_pedido():
        if liberar_num_pedido == 1:
            conn = conectar()
            novo_max_id = conn.execute("SELECT MAX(id) FROM vendas").fetchone()[0]
            conn.close()
            prox_id = (novo_max_id or 0) + 1
            lbl_num_pedido.configure(text=f"PRÓXIMO PEDIDO: #{prox_id}")

    def limpar_caixa():
        estado["carrinho"] = []
        estado["subtotal"] = 0.0
        atualizar_ui_caixa()
        lbl_tot.configure(text="TOTAL: R$ 0,00")
        ent_desc.delete(0, 'end')
        ent_desc.insert(0, "0")
        ent_busca_cli.delete(0, 'end')
        buscar_cliente_venda()
        cb_parcelas.set("1x")
        atualizar_numero_pedido()

    def buscar_cliente_venda(*args):
        f = ent_busca_cli.get()
        conn = conectar()
        clis = conn.execute("SELECT id, nome FROM clientes WHERE nome LIKE ?", (f"%{f}%",)).fetchall()
        conn.close()
        
        lista = ["0 - Consumidor"] + [f"{c[0]} - {c[1]}" for c in clis]
        cb_cliente.configure(values=lista)
        cb_cliente.set(lista[0])

    def buscar_produto_venda(*args):
        f = ent_busca_prod.get()
        conn = conectar()
        try:
            prods = conn.execute("SELECT id, nome, preco FROM produtos WHERE nome LIKE ? OR id LIKE ? OR cod_barras LIKE ?", (f"%{f}%", f"%{f}%", f"%{f}%")).fetchall()
        except:
            prods = conn.execute("SELECT id, nome, preco FROM produtos WHERE nome LIKE ? OR id LIKE ?", (f"%{f}%", f"%{f}%")).fetchall()
        conn.close()
        
        if prods:
            lista = [f"{p[0]} - {p[1]} | R$ {p[2]:.2f}" for p in prods]
        else:
            lista = ["Nenhum produto encontrado"]
            
        cb_produto.configure(values=lista)
        cb_produto.set(lista[0])

    def recalcular_total(*args):
        try:
            desc_str = ent_desc.get().replace(",", ".")
            d = float(desc_str) if desc_str else 0.0
            total_final = max(0, estado["subtotal"] - d)
            lbl_tot.configure(text=f"TOTAL: R$ {total_final:.2f}")
        except:
            pass

    def venda_add(*args):
        selecao = cb_produto.get()
        if selecao in ["Selecione um produto", "Nenhum produto encontrado"]:
            messagebox.showwarning("Aviso", "Selecione um produto válido na lista!")
            return
            
        partes = selecao.split(" | R$ ")
        id_nome = partes[0]
        preco_bd = float(partes[1])
        
        id_prod = id_nome.split(" - ")[0]
        nome_prod = id_nome.split(" - ", 1)[1]
        
        pr_dig = ent_preco_alt.get().replace(",", ".")
        if pr_dig != "":
            try: p_fin = float(pr_dig)
            except ValueError: p_fin = preco_bd
        else:
            p_fin = preco_bd
            
        try:
            qtd = int(ent_qtd.get())
            if qtd <= 0: qtd = 1
        except: qtd = 1
            
        subtotal_item = p_fin * qtd
            
        estado["carrinho"].append({
            'id': int(id_prod), 
            'nome': nome_prod, 
            'preco_unit': p_fin, 
            'qtd': int(qtd), 
            'preco': subtotal_item 
        })
        
        estado["subtotal"] += subtotal_item
        atualizar_ui_caixa()
        
        ent_busca_prod.delete(0, 'end')
        ent_preco_alt.delete(0, 'end')
        ent_qtd.delete(0, 'end')
        ent_qtd.insert(0, "1")
        buscar_produto_venda()
        ent_busca_prod.focus()

    def atualizar_ui_caixa():
        for widget in frame_lista_caixa.winfo_children(): widget.destroy()
            
        f_cabecalho = ctk.CTkFrame(frame_lista_caixa, fg_color="transparent")
        f_cabecalho.pack(fill="x", pady=(0, 5))
        
        ctk.CTkLabel(f_cabecalho, text="QTD", width=40, anchor="center", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="PRODUTO", width=250, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="V. UNIT", width=100, anchor="e", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="TOTAL", width=100, anchor="e", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        for index, item in enumerate(estado["carrinho"]):
            f_item = ctk.CTkFrame(frame_lista_caixa)
            f_item.pack(fill="x", pady=2)
            
            ctk.CTkLabel(f_item, text=f"{item['qtd']}x", width=40, anchor="center").pack(side="left", padx=5)
            ctk.CTkLabel(f_item, text=f"{item['nome']}", width=250, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(f_item, text=f"R$ {item['preco_unit']:.2f}", width=100, anchor="e").pack(side="left", padx=5)
            ctk.CTkLabel(f_item, text=f"R$ {item['preco']:.2f}", width=100, anchor="e", text_color="#2ecc71").pack(side="left", padx=5)
            
            if cargo_usuario in ["Admin", "Gerente", "Desenvolvedor"]:
                btn_rem = ctk.CTkButton(f_item, text="X", width=30, fg_color="#c0392b", hover_color="#e74c3c", command=lambda i=index: remover_item_especifico(i))
                btn_rem.pack(side="right", padx=10)
                
        recalcular_total()

    def remover_item_especifico(index):
        item_rem = estado["carrinho"].pop(index)
        estado["subtotal"] -= item_rem['preco']
        atualizar_ui_caixa()

    def processar_operacao(eh_orcamento=False):
        if not estado["carrinho"]:
            messagebox.showwarning("Aviso", "O carrinho está vazio!")
            return
            
        cid = cb_cliente.get().split(" - ")[0]
        pag = cb_pagto.get()
        
        vendedor_final = 1 
        if cb_vendedor:
            try: vendedor_final = int(cb_vendedor.get().split(" - ")[0])
            except: vendedor_final = 1
        
        desc_str = ent_desc.get().replace(",", ".")
        dsc = float(desc_str) if desc_str else 0.0
        
        tot = estado["subtotal"] - dsc
        data = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        qtd_parcelas = int(cb_parcelas.get().replace("x", "")) if pag == "A Prazo" else 1
        
        if eh_orcamento:
            status = "Orcamento"
        else:
            status = "Pendente" if pag == "A Prazo" else "Pago"
            
        conn = conectar()
        cur = conn.cursor()
        
        cur.execute("INSERT INTO vendas (cliente_id, vendedor_id, valor_total, data_hora, forma_pagto, status) VALUES (?,?,?,?,?,?)", 
                    (cid, vendedor_final, tot, data, pag, status))
        vid = cur.lastrowid
        
        for item in estado["carrinho"]:
            cur.execute("INSERT INTO itens_venda (venda_id, produto_id, nome_produto, preco, quantidade) VALUES (?,?,?,?,?)", 
                        (vid, int(item['id']), item['nome'], item['preco'], int(item['qtd'])))
            
            if not eh_orcamento:
                cur.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (int(item['qtd']), int(item['id'])))
        
        if pag == "A Prazo" and not eh_orcamento:
            base_parc = int(tot / qtd_parcelas)
            lista_parcelas = [base_parc] * qtd_parcelas
            resto = round(tot - sum(lista_parcelas), 2)
            int_resto = int(resto)
            frac_resto = round(resto - int_resto, 2)
            
            for i in range(int_resto): lista_parcelas[-(i+1)] += 1
            lista_parcelas[0] = round(lista_parcelas[0] + frac_resto, 2)
            
            for i in range(qtd_parcelas):
                venc = (datetime.now() + timedelta(days=30*(i+1))).strftime("%Y-%m-%d")
                cur.execute("INSERT INTO parcelas (venda_id, numero_parcela, valor, data_vencimento, status) VALUES (?,?,?,?,?)", 
                            (vid, i+1, lista_parcelas[i], venc, "Pendente"))

        conn.commit()
        conn.close()
        
        if eh_orcamento:
            registrar_log(usuario_logado, f"Gerou o Orçamento #{vid} (Valor: R$ {tot:.2f}). O estoque não foi afetado.")
            messagebox.showinfo("Orçamento Gerado", f"Orçamento #{vid} salvo com sucesso!\nO estoque NÃO foi alterado.\n\nVocê pode gerar o PDF do orçamento na aba 'Editar Vendas'.")
        else:
            registrar_log(usuario_logado, f"Finalizou a Venda #{vid} (Valor: R$ {tot:.2f}, Pagto: {pag}). Estoque reduzido.")
            msg_parcelas = f"\nForam geradas {qtd_parcelas} parcelas para este cliente." if pag == "A Prazo" else ""
            messagebox.showinfo("Venda Finalizada", f"Venda #{vid} finalizada com sucesso! O estoque foi reduzido.{msg_parcelas}")
            
        limpar_caixa()

    ent_busca_cli.bind("<KeyRelease>", buscar_cliente_venda)
    ent_busca_prod.bind("<KeyRelease>", buscar_produto_venda)
    ent_preco_alt.bind("<Return>", venda_add)
    ent_qtd.bind("<Return>", venda_add) 
    ent_desc.bind("<KeyRelease>", recalcular_total)
    
    btn_add.configure(command=venda_add)
    btn_finalizar.configure(command=lambda: processar_operacao(eh_orcamento=False))
    
    if liberar_orcamentos == 1:
        btn_orcamento.configure(command=lambda: processar_operacao(eh_orcamento=True))

    buscar_cliente_venda()
    buscar_produto_venda()
    atualizar_ui_caixa()
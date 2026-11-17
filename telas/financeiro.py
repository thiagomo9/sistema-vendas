import customtkinter as ctk
import sqlite3
import os
from datetime import datetime, timedelta
from tkinter import messagebox, simpledialog

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    PDF_DISPONIVEL = True
except ImportError:
    PDF_DISPONIVEL = False

from database import conectar, DIRETORIO_BASE, DB_PATH, registrar_log, verificar_permissao

# =================================================================
# FUNÇÃO GLOBAL PARA GERAR CUPONS/ORÇAMENTOS EM PDF (DESIGN PREMIUM)
# =================================================================
def gerar_pdf_recibo_cupom(vid, data_venda, subtotal, desconto, tot, pag, lista_itens, subtitulo="CUPOM NÃO FISCAL", nome_cliente="Consumidor"):
    if not PDF_DISPONIVEL:
        messagebox.showerror("Erro", "Biblioteca reportlab não instalada. O PDF não pode ser gerado.")
        return
        
    pasta_recibos = os.path.join(DIRETORIO_BASE, "recibos")
    if not os.path.exists(pasta_recibos):
        os.makedirs(pasta_recibos)
        
    path = os.path.join(pasta_recibos, f"venda_{vid}.pdf")
    
    conn = conectar()
    emp = conn.execute("SELECT nome, cnpj, endereco, telefone FROM empresa WHERE id=1").fetchone()
    conn.close()
    
    nome_emp = emp[0] if emp else "EMPRESA"
    cnpj_emp = emp[1] if emp else ""
    end_emp = emp[2] if emp else ""
    tel_emp = emp[3] if emp else ""

    largura = 80 * mm
    altura = (130 + (len(lista_itens) * 6)) * mm 
    
    cnv = canvas.Canvas(path, pagesize=(largura, altura))
    y = altura - (10 * mm)
    
    cnv.setFont("Helvetica-Bold", 12)
    cnv.drawCentredString(largura/2, y, nome_emp)
    y -= 5 * mm
    
    cnv.setFont("Helvetica", 8)
    if cnpj_emp:
        cnv.drawCentredString(largura/2, y, f"CNPJ: {cnpj_emp}")
        y -= 4 * mm
    if end_emp:
        cnv.drawCentredString(largura/2, y, end_emp)
        y -= 4 * mm
    if tel_emp:
        cnv.drawCentredString(largura/2, y, f"Tel: {tel_emp}")
        y -= 6 * mm
    
    cnv.setStrokeColorRGB(0.5, 0.5, 0.5)
    cnv.setDash(2, 2)
    cnv.line(5 * mm, y, largura - (5 * mm), y)
    y -= 6 * mm
    
    cnv.setFont("Helvetica-Bold", 11)
    cnv.drawCentredString(largura/2, y, subtitulo)
    y -= 8 * mm
    
    cnv.setFont("Helvetica", 8)
    label_pedido = "Orçamento:" if "ORÇAMENTO" in subtitulo else "Pedido:"
    cnv.drawString(5 * mm, y, f"{label_pedido} #{vid}")
    cnv.drawRightString(largura - (5 * mm), y, data_venda[:16])
    y -= 5 * mm
    
    cnv.setFont("Helvetica-Bold", 9)
    cnv.drawString(5 * mm, y, f"Cliente: {nome_cliente[:25]}")
    y -= 6 * mm

    cnv.line(5 * mm, y, largura - (5 * mm), y)
    y -= 5 * mm
    
    cnv.setFont("Helvetica-Bold", 8)
    cnv.drawString(5 * mm, y, "QTD")
    cnv.drawString(15 * mm, y, "DESCRIÇÃO")
    cnv.drawRightString(largura - (5 * mm), y, "VALOR")
    y -= 4 * mm
    
    cnv.line(5 * mm, y, largura - (5 * mm), y)
    y -= 5 * mm
    
    cnv.setFont("Helvetica", 8)
    for i in lista_itens:
        qtd = i.get('qtd', 1)
        nome_curto = i['nome'][:18] 
        
        cnv.drawString(5 * mm, y, f"{qtd:02d}")
        cnv.drawString(15 * mm, y, nome_curto)
        cnv.drawRightString(largura - (5 * mm), y, f"R$ {i['preco']:.2f}")
        y -= 5 * mm
        
    cnv.line(5 * mm, y, largura - (5 * mm), y)
    y -= 6 * mm
    
    cnv.setFont("Helvetica", 9)
    cnv.drawString(5 * mm, y, "Subtotal:")
    cnv.drawRightString(largura - (5 * mm), y, f"R$ {subtotal:.2f}")
    y -= 5 * mm
    
    if desconto > 0:
        cnv.drawString(5 * mm, y, "Desconto:")
        cnv.drawRightString(largura - (5 * mm), y, f"- R$ {desconto:.2f}")
        y -= 5 * mm
        
    y -= 2 * mm
    cnv.setFont("Helvetica-Bold", 13)
    cnv.drawString(5 * mm, y, "TOTAL:")
    cnv.drawRightString(largura - (5 * mm), y, f"R$ {tot:.2f}")
    y -= 8 * mm
    
    cnv.setFont("Helvetica-Bold", 9)
    label_pag = "Pagamento Previsto:" if "ORÇAMENTO" in subtitulo else "Pagamento:"
    cnv.drawString(5 * mm, y, label_pag)
    cnv.drawRightString(largura - (5 * mm), y, pag)
    y -= 8 * mm
    
    cnv.line(5 * mm, y, largura - (5 * mm), y)
    y -= 6 * mm
    
    cnv.setFont("Helvetica", 8)
    if "ORÇAMENTO" in subtitulo:
        cnv.drawCentredString(largura/2, y, "Este documento não é válido como recibo.")
        cnv.drawCentredString(largura/2, y - (4 * mm), "Válido por 15 dias.")
    else:
        cnv.drawCentredString(largura/2, y, "Obrigado pela preferência!")
        cnv.drawCentredString(largura/2, y - (4 * mm), "Volte sempre!")
    
    cnv.save()
    os.startfile(os.path.abspath(path))


# =================================================================
# ESTRUTURA PRINCIPAL DO MÓDULO FINANCEIRO
# =================================================================
def setup_financeiro(container, usuario_logado, cargo_usuario):
    conn = conectar()
    conf = conn.execute("SELECT ver_contas_pagar FROM configuracoes WHERE id=1").fetchone()
    conn.close()
    
    liberar_pagar = conf[0] if conf else 1

    tabview = ctk.CTkTabview(container)
    tabview.pack(fill="both", expand=True)
    
    if verificar_permissao(cargo_usuario, "aba_editar_vendas"):
        tabview.add("🔄 Editar Vendas")
        render_aba_editar_vendas(tabview.tab("🔄 Editar Vendas"), usuario_logado, cargo_usuario)
        
    if verificar_permissao(cargo_usuario, "aba_receber"):
        tabview.add("📥 A Receber")
        render_aba_receber(tabview.tab("📥 A Receber"), usuario_logado, cargo_usuario)
        
    if verificar_permissao(cargo_usuario, "aba_pagar") and (liberar_pagar == 1 or cargo_usuario == "Desenvolvedor"):
        tabview.add("📤 A Pagar")
        render_aba_pagar(tabview.tab("📤 A Pagar"), usuario_logado, cargo_usuario)
        
    if verificar_permissao(cargo_usuario, "menu_historico"):
        tabview.add("📜 Histórico")
        render_aba_historico(tabview.tab("📜 Histórico"), usuario_logado, cargo_usuario)
        
    if verificar_permissao(cargo_usuario, "aba_relatorios"):
        tabview.add("📊 Relatórios")
        render_aba_relatorios(tabview.tab("📊 Relatórios"), usuario_logado, cargo_usuario, liberar_pagar)


# =========================================================
# ABA: EDITAR VENDAS E CONVERTER ORÇAMENTOS
# =========================================================
def render_aba_editar_vendas(tab, usuario_logado, cargo_usuario):
    ctk.CTkLabel(tab, text="EDIÇÃO DE VENDAS E CONVERSÃO DE ORÇAMENTOS", font=("Arial", 20, "bold")).pack(pady=10)
    
    edicao = {
        "venda_id": None, "cliente_nome": "", "cliente_id": 0, "data_venda": "", 
        "forma_pagto_orig": "", "status_orig": "",
        "itens_originais": [], "itens_novos": [], "itens_removidos": []  
    }

    conn = conectar()
    clis_db = conn.execute("SELECT id, nome FROM clientes ORDER BY nome ASC").fetchall()
    conn.close()
    lista_clientes = ["0 - Consumidor"] + [f"{c[0]} - {c[1]}" for c in clis_db]

    f_topo = ctk.CTkFrame(tab)
    f_topo.pack(fill="x", padx=20, pady=5)
    
    ctk.CTkLabel(f_topo, text="Busca ID:").pack(side="left", padx=(5, 2))
    ent_id_venda = ctk.CTkEntry(f_topo, width=70)
    ent_id_venda.pack(side="left", padx=2)
    btn_buscar = ctk.CTkButton(f_topo, text="BUSCAR", width=70)
    btn_buscar.pack(side="left", padx=2)
    
    ctk.CTkLabel(f_topo, text=" | Cliente:").pack(side="left", padx=(5, 2))
    cb_cliente_edicao = ctk.CTkComboBox(f_topo, values=lista_clientes, width=160)
    cb_cliente_edicao.pack(side="left", padx=2)
    
    ctk.CTkLabel(f_topo, text=" | Add Produto:").pack(side="left", padx=(5, 2))
    ent_add = ctk.CTkEntry(f_topo, placeholder_text="Nome ou ID...", width=140)
    ent_add.pack(side="left", padx=2)
    ent_qtd_add = ctk.CTkEntry(f_topo, width=40)
    ent_qtd_add.pack(side="left", padx=2); ent_qtd_add.insert(0, "1")
    btn_add = ctk.CTkButton(f_topo, text="ADD", fg_color="green", width=50)
    btn_add.pack(side="left", padx=5)
    
    txt_detalhes = ctk.CTkTextbox(tab, font=("Courier New", 14), height=80)
    txt_detalhes.pack(fill="x", padx=20, pady=5)
    frame_itens = ctk.CTkScrollableFrame(tab, fg_color="#1e1e1e")
    frame_itens.pack(fill="both", expand=True, padx=20, pady=5)
    
    f_rodape = ctk.CTkFrame(tab)
    f_rodape.pack(fill="x", padx=20, pady=(5, 15))
    
    conn = conectar()
    try: f_pag = [f[0] for f in conn.execute("SELECT nome FROM formas_pagto").fetchall()]
    except: f_pag = ["Dinheiro", "Pix", "Cartão", "A Prazo"]
    conn.close()
    
    cb_novo_pagto = ctk.CTkComboBox(f_rodape, values=f_pag, width=150)
    cb_novo_pagto.pack(side="left", padx=5)
    
    btn_salvar = ctk.CTkButton(f_rodape, text="💾 SALVAR ALTERAÇÕES", fg_color="#f39c12", text_color="black")
    btn_salvar.pack(side="left", padx=10)
    
    btn_converter = ctk.CTkButton(f_rodape, text="CONVERTER ORÇAMENTO EM VENDA", fg_color="green")
    
    btn_estornar = ctk.CTkButton(f_rodape, text="CANCELAR / ESTORNAR", fg_color="#c0392b")
    btn_estornar.pack(side="right", padx=10)

    btn_recibo = ctk.CTkButton(f_rodape, text="GERAR PDF", fg_color="#2980b9")
    btn_recibo.pack(side="right", padx=10)

    def buscar():
        vid = ent_id_venda.get().strip()
        if not vid: return
        edicao["venda_id"] = None
        edicao["itens_originais"] = []
        edicao["itens_novos"] = []
        edicao["itens_removidos"] = []

        conn = conectar()
        v = conn.execute("SELECT v.id, c.nome, v.valor_total, v.data_hora, v.forma_pagto, v.status, v.cliente_id FROM vendas v LEFT JOIN clientes c ON v.cliente_id=c.id WHERE v.id=?", (vid,)).fetchone()
        
        if not v: 
            txt_detalhes.delete("1.0", "end")
            txt_detalhes.insert("end", "Registro não encontrado!")
            for w in frame_itens.winfo_children(): w.destroy()
            btn_converter.pack_forget()
            cb_cliente_edicao.set("0 - Consumidor")
            conn.close()
            return
            
        itens = conn.execute("SELECT id, produto_id, nome_produto, preco, quantidade FROM itens_venda WHERE venda_id=?", (vid,)).fetchall()
        conn.close()

        edicao["venda_id"] = v[0]
        edicao["cliente_nome"] = v[1] or 'Consumidor'
        edicao["cliente_id"] = v[6] if v[6] is not None else 0
        edicao["data_venda"] = v[3]
        edicao["forma_pagto_orig"] = v[4]
        edicao["status_orig"] = v[5]

        if edicao["cliente_id"] != 0:
            cb_cliente_edicao.set(f"{edicao['cliente_id']} - {edicao['cliente_nome']}")
        else:
            cb_cliente_edicao.set("0 - Consumidor")

        for i in itens:
            edicao["itens_originais"].append({'id_registro': i[0], 'produto_id': i[1], 'nome': i[2], 'preco': i[3], 'qtd': i[4] or 1})

        cb_novo_pagto.set(v[4])
        atualizar_ui_edicao()

    def atualizar_ui_edicao():
        for w in frame_itens.winfo_children(): w.destroy()
        txt_detalhes.delete("1.0", "end")
        if not edicao["venda_id"]: return
        
        try: d_venda = datetime.strptime(edicao["data_venda"], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        except: d_venda = edicao["data_venda"][:16]

        total = sum(i['preco'] for i in edicao["itens_originais"]) + sum(i['preco'] for i in edicao["itens_novos"])
        
        aviso = ""
        cliente_combo = cb_cliente_edicao.get()
        cli_id_selecionado = int(cliente_combo.split(" - ")[0]) if " - " in cliente_combo else 0
        
        if edicao["itens_novos"] or edicao["itens_removidos"] or cb_novo_pagto.get() != edicao["forma_pagto_orig"] or cli_id_selecionado != edicao["cliente_id"]:
            aviso = " (ALTERAÇÕES NÃO SALVAS ⚠️)"
            
        tipo_doc = "ORÇAMENTO (NÃO AFETA ESTOQUE/CAIXA)" if edicao["status_orig"] == "Orcamento" else "VENDA"
        nome_cliente_mostrar = cliente_combo.split(" - ", 1)[1] if " - " in cliente_combo else "Consumidor"
            
        txt_detalhes.insert("end", f"{tipo_doc} #{edicao['venda_id']} | Data: {d_venda}\nCliente: {nome_cliente_mostrar} | Pagto Atual: {edicao['forma_pagto_orig']} | Status: {edicao['status_orig']}\nNOVO TOTAL CALCULADO: R$ {total:.2f}{aviso}")

        if edicao["status_orig"] == "Orcamento":
            btn_converter.pack(side="left", padx=10)
        else:
            btn_converter.pack_forget()

        for idx, i in enumerate(edicao["itens_originais"]):
            fi = ctk.CTkFrame(frame_itens)
            fi.pack(fill="x", pady=2)
            ctk.CTkLabel(fi, text=f"{i['qtd']}x {i['nome']}", width=300, anchor="w").pack(side="left", padx=10)
            ctk.CTkLabel(fi, text=f"R$ {i['preco']:.2f}", width=100, anchor="e").pack(side="left", padx=10)
            if edicao["status_orig"] != 'Cancelado':
                ctk.CTkButton(fi, text="X", width=30, fg_color="red", command=lambda x=idx: remover_orig(x)).pack(side="right", padx=10)

        for idx, i in enumerate(edicao["itens_novos"]):
            fi = ctk.CTkFrame(frame_itens)
            fi.pack(fill="x", pady=2)
            ctk.CTkLabel(fi, text=f"[NOVO] {i['qtd']}x {i['nome']}", width=300, anchor="w", text_color="green").pack(side="left", padx=10)
            ctk.CTkLabel(fi, text=f"R$ {i['preco']:.2f}", width=100, anchor="e", text_color="green").pack(side="left", padx=10)
            if edicao["status_orig"] != 'Cancelado':
                ctk.CTkButton(fi, text="X", width=30, fg_color="red", command=lambda x=idx: remover_novo(x)).pack(side="right", padx=10)

    def remover_orig(idx):
        item = edicao["itens_originais"].pop(idx)
        edicao["itens_removidos"].append(item) 
        atualizar_ui_edicao()

    def remover_novo(idx):
        edicao["itens_novos"].pop(idx)
        atualizar_ui_edicao()

    def add_item():
        t = ent_add.get().strip()
        if not t: return
        if edicao["status_orig"] == 'Cancelado': return

        conn = conectar()
        p = conn.execute("SELECT id, nome, preco FROM produtos WHERE id=? OR nome LIKE ?", (t, f"%{t}%")).fetchone()
        conn.close()
        if p:
            try: qtd = int(ent_qtd_add.get())
            except: qtd = 1
            if qtd <= 0: qtd = 1
            preco_final = p[2] * qtd
            edicao["itens_novos"].append({"produto_id": p[0], "nome": p[1], "preco": preco_final, "qtd": qtd})
            ent_add.delete(0, 'end')
            ent_qtd_add.delete(0, 'end'); ent_qtd_add.insert(0, "1")
            atualizar_ui_edicao()

    def salvar():
        vid = edicao["venda_id"]
        if not vid or edicao["status_orig"] == 'Cancelado': return
            
        novo_pag = cb_novo_pagto.get()
        if not novo_pag: return
        
        cliente_str = cb_cliente_edicao.get()
        novo_cliente_id = int(cliente_str.split(" - ")[0]) if " - " in cliente_str else 0

        total_novo = sum(i['preco'] for i in edicao["itens_originais"]) + sum(i['preco'] for i in edicao["itens_novos"])
        eh_orcamento = edicao["status_orig"] == "Orcamento"

        conn = conectar()
        if not eh_orcamento and edicao["forma_pagto_orig"] == "A Prazo":
            pagas = conn.execute("SELECT COUNT(*) FROM parcelas WHERE venda_id=? AND status='Pago'", (vid,)).fetchone()[0]
            if pagas > 0:
                messagebox.showerror("Erro", "Venda possui parcelas pagas. Estorne na aba 'A Receber' antes de editar o valor total.")
                conn.close(); return

        if messagebox.askyesno("Salvar", f"Salvar alterações do registro #{vid}?"):
            cur = conn.cursor()
            
            for item in edicao["itens_removidos"]:
                cur.execute("DELETE FROM itens_venda WHERE id=?", (item['id_registro'],))
                if not eh_orcamento and item['produto_id']:
                    cur.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (item['qtd'], item['produto_id']))
                
            for item in edicao["itens_novos"]:
                cur.execute("INSERT INTO itens_venda (venda_id, produto_id, nome_produto, preco, quantidade) VALUES (?,?,?,?,?)", 
                            (vid, item['produto_id'], item['nome'], item['preco'], item['qtd']))
                if not eh_orcamento and item['produto_id']:
                    cur.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item['qtd'], item['produto_id']))
            
            status_novo = edicao["status_orig"]
            if not eh_orcamento:
                cur.execute("DELETE FROM parcelas WHERE venda_id=?", (vid,))
                status_novo = "Pago"
                if novo_pag == "A Prazo":
                    dialog = ctk.CTkInputDialog(text="Quantas parcelas?", title="Parcelamento")
                    try:
                        qtd_parcelas = int(dialog.get_input())
                        if qtd_parcelas <= 0: raise ValueError
                        
                        status_novo = "Pendente"
                        base_parc = int(total_novo / qtd_parcelas)
                        lista_parcelas = [base_parc] * qtd_parcelas
                        resto = round(total_novo - sum(lista_parcelas), 2)
                        int_resto = int(resto)
                        frac_resto = round(resto - int_resto, 2)
                        for i in range(int_resto): lista_parcelas[-(i+1)] += 1
                        lista_parcelas[0] = round(lista_parcelas[0] + frac_resto, 2)
                        for i in range(qtd_parcelas):
                            venc = (datetime.now() + timedelta(days=30*(i+1))).strftime("%Y-%m-%d")
                            cur.execute("INSERT INTO parcelas (venda_id, numero_parcela, valor, data_vencimento, status) VALUES (?,?,?,?,?)", 
                                        (vid, i+1, lista_parcelas[i], venc, "Pendente"))
                    except:
                        pass

            cur.execute("UPDATE vendas SET valor_total=?, forma_pagto=?, status=?, cliente_id=? WHERE id=?", (total_novo, novo_pag, status_novo, novo_cliente_id, vid))
            conn.commit()
            
            msg = "Orçamento atualizado (Sem impacto no estoque)." if eh_orcamento else "Venda, Estoque e Cliente atualizados com sucesso."
            registrar_log(usuario_logado, f"Salvou edições no registro #{vid}.")
            messagebox.showinfo("Sucesso", msg)
            
        conn.close()
        buscar()

    def converter_orcamento():
        vid = edicao["venda_id"]
        if not vid or edicao["status_orig"] != "Orcamento": return
        
        cliente_str = cb_cliente_edicao.get()
        cli_id_selec = int(cliente_str.split(" - ")[0]) if " - " in cliente_str else 0
        
        if edicao["itens_novos"] or edicao["itens_removidos"] or cli_id_selec != edicao["cliente_id"]:
            messagebox.showwarning("Atenção", "Existem alterações não salvas (produtos ou cliente).\nSalve as alterações antes de converter o orçamento em venda.")
            return

        pag = cb_novo_pagto.get()
        if messagebox.askyesno("Confirmar Faturamento", f"Converter Orçamento #{vid} em VENDA?\n\n- O estoque dos produtos será reduzido agora.\n- O valor entrará no caixa (ou gerará parcelas se for A Prazo)."):
            conn = conectar()
            cur = conn.cursor()
            
            status_novo = "Pago"
            total = sum(i['preco'] for i in edicao["itens_originais"])
            
            for item in edicao["itens_originais"]:
                if item['produto_id']:
                    cur.execute("UPDATE produtos SET estoque = estoque - ? WHERE id = ?", (item['qtd'], item['produto_id']))
            
            if pag == "A Prazo":
                dialog = ctk.CTkInputDialog(text="Quantas parcelas para esta venda?", title="Parcelamento")
                try:
                    qtd_parcelas = int(dialog.get_input())
                    if qtd_parcelas > 0:
                        status_novo = "Pendente"
                        base_parc = int(total / qtd_parcelas)
                        lista_parcelas = [base_parc] * qtd_parcelas
                        resto = round(total - sum(lista_parcelas), 2)
                        int_resto = int(resto)
                        frac_resto = round(resto - int_resto, 2)
                        for i in range(int_resto): lista_parcelas[-(i+1)] += 1
                        lista_parcelas[0] = round(lista_parcelas[0] + frac_resto, 2)
                        for i in range(qtd_parcelas):
                            venc = (datetime.now() + timedelta(days=30*(i+1))).strftime("%Y-%m-%d")
                            cur.execute("INSERT INTO parcelas (venda_id, numero_parcela, valor, data_vencimento, status) VALUES (?,?,?,?,?)", 
                                        (vid, i+1, lista_parcelas[i], venc, "Pendente"))
                except:
                    pass

            cur.execute("UPDATE vendas SET status=?, forma_pagto=? WHERE id=?", (status_novo, pag, vid))
            conn.commit()
            conn.close()
            
            registrar_log(usuario_logado, f"Converteu Orçamento #{vid} em Venda Faturada.")
            messagebox.showinfo("Venda Faturada", "O Orçamento foi faturado com sucesso!\nEstoque reduzido e fluxo de caixa atualizado.")
            buscar()

    def estornar():
        vid = edicao["venda_id"]
        eh_orcamento = edicao["status_orig"] == "Orcamento"
        
        msg_aviso = "Cancelar este Orçamento? O estoque NÃO será afetado." if eh_orcamento else "Cancelar esta Venda e DEVOLVER os produtos ao estoque?"
        
        if vid and messagebox.askyesno("CUIDADO", msg_aviso):
            conn = conectar()
            if not eh_orcamento:
                itens = conn.execute("SELECT produto_id, quantidade FROM itens_venda WHERE venda_id=?", (vid,)).fetchall()
                for prod_id, qtd in itens:
                    if prod_id:
                        conn.execute("UPDATE produtos SET estoque = estoque + ? WHERE id = ?", (qtd or 1, prod_id))
            
            conn.execute("UPDATE vendas SET status='Cancelado', valor_total=0 WHERE id=?", (vid,))
            conn.execute("UPDATE parcelas SET status='Cancelado' WHERE venda_id=?", (vid,))
            conn.commit()
            conn.close()
            
            registrar_log(usuario_logado, f"Cancelou o registro #{vid}.")
            buscar()

    def gerar_recibo():
        vid = edicao["venda_id"]
        if not vid: return messagebox.showwarning("Aviso", "Busque um registro primeiro!")
        
        cliente_combo = cb_cliente_edicao.get()
        cli_id_selec = int(cliente_combo.split(" - ")[0]) if " - " in cliente_combo else 0
        
        if edicao["itens_novos"] or edicao["itens_removidos"] or cb_novo_pagto.get() != edicao["forma_pagto_orig"] or cli_id_selec != edicao["cliente_id"]:
            messagebox.showwarning("Aviso", "Existem alterações não salvas!\nClique em 'SALVAR ALTERAÇÕES' antes de imprimir.")
            return
            
        conn = conectar()
        venda = conn.execute("SELECT id, data_hora, valor_total, forma_pagto, status FROM vendas WHERE id=?", (vid,)).fetchone()
        itens_bd = conn.execute("SELECT nome_produto, preco, quantidade FROM itens_venda WHERE venda_id=?", (vid,)).fetchall()
        conn.close()
        
        lista_itens = [{'nome': i[0], 'preco': i[1], 'qtd': i[2] if len(i)>2 and i[2] is not None else 1} for i in itens_bd]
        subtotal = sum(i['preco'] for i in lista_itens)
        desconto = subtotal - venda[2] if subtotal > venda[2] else 0.0
        
        try: d_venda = datetime.strptime(venda[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        except: d_venda = venda[1][:16]
        
        subtitulo = "ORÇAMENTO - SEM VALOR FISCAL" if venda[4] == "Orcamento" else "CUPOM NÃO FISCAL"
        
        nome_cliente_pdf = cliente_combo.split(" - ", 1)[1] if " - " in cliente_combo else "Consumidor"
        
        gerar_pdf_recibo_cupom(venda[0], d_venda, subtotal, desconto, venda[2], venda[3], lista_itens, subtitulo, nome_cliente_pdf)

    ent_id_venda.bind("<Return>", lambda e: buscar())
    ent_add.bind("<Return>", lambda e: add_item())
    ent_qtd_add.bind("<Return>", lambda e: add_item())
    cb_novo_pagto.configure(command=lambda e: atualizar_ui_edicao())
    cb_cliente_edicao.configure(command=lambda e: atualizar_ui_edicao())
    
    btn_buscar.configure(command=buscar)
    btn_add.configure(command=add_item)
    btn_salvar.configure(command=salvar)
    btn_converter.configure(command=converter_orcamento)
    btn_estornar.configure(command=estornar)
    btn_recibo.configure(command=gerar_recibo)


# =========================================================
# ABA: A RECEBER
# =========================================================
def render_aba_receber(tab, usuario_logado, cargo_usuario):
    ctk.CTkLabel(tab, text="CONTROLE DE PARCELAS E RECEBIMENTOS", font=("Arial", 20, "bold")).pack(pady=10)
    
    f_top1 = ctk.CTkFrame(tab, fg_color="transparent")
    f_top1.pack(fill="x", padx=20, pady=(10, 0))
    ctk.CTkLabel(f_top1, text="Status:").pack(side="left", padx=(0, 5))
    cb_status = ctk.CTkComboBox(f_top1, values=["Todas Pendentes", "Vencidas", "A Vencer Hoje", "A Vencer", "Todas (Inclui Pagas)"], width=180)
    cb_status.pack(side="left", padx=5)

    f_top2 = ctk.CTkFrame(tab, fg_color="transparent")
    f_top2.pack(fill="x", padx=20, pady=(5, 10))
    ctk.CTkLabel(f_top2, text="Cliente:").pack(side="left", padx=(0, 5))
    ent_cliente = ctk.CTkEntry(f_top2, placeholder_text="Buscar devedor...", width=150)
    ent_cliente.pack(side="left", padx=5)
    ctk.CTkLabel(f_top2, text="De:").pack(side="left", padx=(10, 5))
    ent_data_ini = ctk.CTkEntry(f_top2, width=110, placeholder_text="DD/MM/AAAA")
    ent_data_ini.pack(side="left", padx=5)
    ctk.CTkLabel(f_top2, text="Até:").pack(side="left", padx=5)
    ent_data_fim = ctk.CTkEntry(f_top2, width=110, placeholder_text="DD/MM/AAAA")
    ent_data_fim.pack(side="left", padx=5)

    frame_lista = ctk.CTkScrollableFrame(tab, fg_color="#1e1e1e")
    frame_lista.pack(fill="both", expand=True, padx=20, pady=10)

    def limpar_filtros():
        cb_status.set("Todas Pendentes")
        ent_cliente.delete(0, 'end')
        ent_data_ini.delete(0, 'end')
        ent_data_fim.delete(0, 'end')
        atualizar_lista()

    def atualizar_lista(*args):
        for w in frame_lista.winfo_children(): w.destroy()
        termo = ent_cliente.get().strip()
        sf = cb_status.get()
        d_ini_str = ent_data_ini.get().strip()
        d_fim_str = ent_data_fim.get().strip()
        hoje = datetime.now().strftime("%Y-%m-%d")

        query = "SELECT p.id, p.venda_id, p.numero_parcela, c.nome, p.valor, p.data_vencimento, p.status, v.valor_total FROM parcelas p JOIN vendas v ON p.venda_id = v.id JOIN clientes c ON v.cliente_id = c.id WHERE c.nome LIKE ? AND p.status != 'Cancelado' "
        params = [f"%{termo}%"]

        if sf == "Todas Pendentes": query += " AND p.status = 'Pendente' "
        elif sf == "Vencidas": query += " AND p.status = 'Pendente' AND p.data_vencimento < ? "; params.append(hoje)
        elif sf == "A Vencer Hoje": query += " AND p.status = 'Pendente' AND p.data_vencimento = ? "; params.append(hoje)
        elif sf == "A Vencer": query += " AND p.status = 'Pendente' AND p.data_vencimento > ? "; params.append(hoje)

        if len(d_ini_str) == 10 and len(d_fim_str) == 10:
            try:
                d_ini_db = datetime.strptime(d_ini_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                d_fim_db = datetime.strptime(d_fim_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                query += " AND p.data_vencimento BETWEEN ? AND ? "
                params.extend([d_ini_db, d_fim_db])
            except: pass
            
        query += " ORDER BY p.status DESC, p.data_vencimento ASC"

        conn = conectar()
        parcelas = conn.execute(query, params).fetchall()
        conn.close()

        f_cabecalho = ctk.CTkFrame(frame_lista, fg_color="transparent")
        f_cabecalho.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(f_cabecalho, text="VENDA", width=60, anchor="center", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="PARC.", width=60, anchor="center", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="CLIENTE", width=250, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="VALOR", width=100, anchor="e", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="VENCIMENTO", width=100, anchor="center", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="STATUS", width=80, anchor="center", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        for p in parcelas:
            f_item = ctk.CTkFrame(frame_lista)
            f_item.pack(fill="x", pady=2)
            ctk.CTkLabel(f_item, text=f"#{p[1]}", width=60, anchor="center").pack(side="left", padx=5)
            ctk.CTkLabel(f_item, text=f"{p[2]}x", width=60, anchor="center").pack(side="left", padx=5)
            ctk.CTkLabel(f_item, text=f"{p[3][:25]}", width=250, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(f_item, text=f"R$ {p[4]:.2f}", width=100, anchor="e").pack(side="left", padx=5)
            
            try: d_br = datetime.strptime(p[5], "%Y-%m-%d").strftime("%d/%m/%Y")
            except: d_br = p[5]
            
            c_data = "white"
            if p[6] == "Pendente":
                if p[5] < hoje: c_data = "#e74c3c" 
                elif p[5] == hoje: c_data = "#f1c40f" 
                
            ctk.CTkLabel(f_item, text=d_br, width=100, text_color=c_data).pack(side="left", padx=5)
            c_stat = "#e74c3c" if p[6] == "Pendente" else "#2ecc71"
            ctk.CTkLabel(f_item, text=p[6], width=80, text_color=c_stat, font=("Arial", 12, "bold")).pack(side="left", padx=5)

            if p[6] == "Pendente":
                btn_receber = ctk.CTkButton(f_item, text="💰 RECEBER", width=90, fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 11, "bold"), command=lambda pid=p[0], num=p[2], v_id=p[1]: receber_parcela(pid, num, v_id))
                btn_receber.pack(side="right", padx=5)
                btn_adiar = ctk.CTkButton(f_item, text="📅 ADIAR", width=90, fg_color="#f39c12", hover_color="#e67e22", text_color="black", font=("Arial", 11, "bold"), command=lambda pid=p[0]: alterar_vencimento_parcela(pid))
                btn_adiar.pack(side="right", padx=5)
            else:
                btn_recibo = ctk.CTkButton(f_item, text="🖨️ RECIBO", width=90, fg_color="#2980b9", hover_color="#3498db", font=("Arial", 11, "bold"), command=lambda pid=p[0], num=p[2], v_id=p[1], val=p[4], cli=p[3], data_v=d_br: gerar_recibo_parcela(pid, num, v_id, val, cli, data_v))
                btn_recibo.pack(side="right", padx=5)
                btn_cancelar = ctk.CTkButton(f_item, text="↩️ CANCELAR", width=90, fg_color="#c0392b", hover_color="#e74c3c", text_color="white", font=("Arial", 11, "bold"), command=lambda pid=p[0], num=p[2], v_id=p[1]: estornar_recebimento_parcela(pid, num, v_id))
                btn_cancelar.pack(side="right", padx=5)

    def alterar_vencimento_parcela(pid):
        dialog = ctk.CTkInputDialog(text="Nova data de vencimento\nFormato: DD/MM/AAAA", title="Adiar")
        d = dialog.get_input()
        if d:
            try:
                data_db = datetime.strptime(d, "%d/%m/%Y").strftime("%Y-%m-%d")
                conn = conectar()
                conn.execute("UPDATE parcelas SET data_vencimento=? WHERE id=?", (data_db, pid))
                conn.commit()
                conn.close()
                registrar_log(usuario_logado, f"Adiou o vencimento da parcela ID #{pid} para {d}")
                atualizar_lista()
                messagebox.showinfo("Ok", "Data atualizada!")
            except:
                messagebox.showerror("Erro", "Formato inválido. Use DD/MM/AAAA (ex: 31/12/2026).")

    def receber_parcela(pid, num, vid):
        if messagebox.askyesno("Confirma", f"Receber Parcela {num} da Venda #{vid}?"):
            conn = conectar()
            conn.execute("UPDATE parcelas SET status='Pago', data_pagamento=? WHERE id=?", (datetime.now().strftime("%Y-%m-%d"), pid))
            
            if conn.execute("SELECT COUNT(*) FROM parcelas WHERE venda_id=? AND status='Pendente'", (vid,)).fetchone()[0] == 0:
                conn.execute("UPDATE vendas SET status='Pago' WHERE id=?", (vid,))
                
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, f"Recebeu a Parcela {num}x da Venda #{vid}")
            atualizar_lista()

    def estornar_recebimento_parcela(pid, num, vid):
        if messagebox.askyesno("Cuidado", f"Deseja cancelar o recebimento da Parcela {num} da Venda #{vid}?\n\nA parcela voltará a ficar 'Pendente'."):
            conn = conectar()
            conn.execute("UPDATE parcelas SET status='Pendente', data_pagamento=NULL WHERE id=?", (pid,))
            conn.execute("UPDATE vendas SET status='Pendente' WHERE id=?", (vid,))
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, f"Estornou o pagamento da Parcela {num}x da Venda #{vid}")
            atualizar_lista()
            messagebox.showinfo("Sucesso", "O recebimento foi estornado e a parcela voltou para o status Pendente.")

    def gerar_recibo_parcela(pid, num, vid, val, cli, dt_v):
        if not PDF_DISPONIVEL: 
            messagebox.showerror("Erro", "A biblioteca reportlab está em falta. Instale via terminal.")
            return
            
        pth = os.path.join(DIRETORIO_BASE, "recibos", f"recibo_parc_{pid}.pdf")
        os.makedirs(os.path.dirname(pth), exist_ok=True)
        
        conn = conectar()
        emp = conn.execute("SELECT nome, cnpj FROM empresa WHERE id=1").fetchone()
        tot_p = conn.execute("SELECT COUNT(*) FROM parcelas WHERE venda_id=?", (vid,)).fetchone()[0]
        conn.close()
        
        cnv = canvas.Canvas(pth, pagesize=(80*mm, 110*mm))
        y = 100*mm
        
        cnv.setFont("Helvetica-Bold", 11)
        cnv.drawCentredString(40*mm, y, emp[0] if emp else "EMPRESA")
        y -= 5*mm
        
        cnv.setFont("Helvetica", 8)
        cnv.drawCentredString(40*mm, y, emp[1] if emp else "")
        y -= 10*mm
        
        cnv.setStrokeColorRGB(0.5, 0.5, 0.5)
        cnv.setDash(2, 2)
        cnv.line(5 * mm, y, 75 * mm, y)
        y -= 6 * mm
        
        cnv.setFont("Helvetica-Bold", 10)
        cnv.drawCentredString(40*mm, y, "RECIBO DE PARCELA")
        y -= 8*mm
        
        cnv.setFont("Helvetica", 9)
        cnv.drawString(5*mm, y, f"Venda: #{vid}")
        y -= 5*mm
        
        cnv.setFont("Helvetica-Bold", 9)
        cnv.drawString(5*mm, y, f"Cliente: {cli[:20]}")
        y -= 5*mm
        
        cnv.setFont("Helvetica", 9)
        cnv.drawString(5*mm, y, f"Parcela: {num} de {tot_p}")
        y -= 8*mm
        
        cnv.line(5 * mm, y, 75 * mm, y)
        y -= 6 * mm
        
        cnv.setFont("Helvetica-Bold", 12)
        cnv.drawString(5*mm, y, "VALOR PAGO:")
        cnv.drawRightString(75*mm, y, f"R$ {val:.2f}")
        y -= 8*mm
        
        cnv.line(5 * mm, y, 75 * mm, y)
        y -= 6 * mm
        
        cnv.setFont("Helvetica", 8)
        cnv.drawString(5*mm, y, f"Vencimento Original: {dt_v}")
        y -= 4*mm
        
        cnv.drawString(5*mm, y, f"Data do Pagamento: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        y -= 10*mm
        
        cnv.drawCentredString(40*mm, y, "Recebimento confirmado com sucesso.")
        cnv.save()
        os.startfile(os.path.abspath(pth))

    cb_status.configure(command=atualizar_lista)
    ent_cliente.bind("<KeyRelease>", atualizar_lista)
    ent_data_ini.bind("<KeyRelease>", atualizar_lista)
    ent_data_fim.bind("<KeyRelease>", atualizar_lista)
    btn_limpar = ctk.CTkButton(f_top2, text="Limpar Filtros", fg_color="gray", width=100, command=limpar_filtros)
    btn_limpar.pack(side="left", padx=10)
    atualizar_lista()


# =========================================================
# ABA: A PAGAR
# =========================================================
def render_aba_pagar(tab, usuario_logado, cargo_usuario):
    ctk.CTkLabel(tab, text="CONTAS A PAGAR E BOLETOS", font=("Arial", 20, "bold")).pack(pady=10)
    
    f_add = ctk.CTkFrame(tab, fg_color="transparent")
    f_add.pack(fill="x", padx=20, pady=(10, 0))
    ctk.CTkLabel(f_add, text="Descrição:").pack(side="left", padx=(0, 5))
    ent_desc = ctk.CTkEntry(f_add, width=250)
    ent_desc.pack(side="left", padx=5)
    ctk.CTkLabel(f_add, text="Valor:").pack(side="left", padx=(10, 5))
    ent_val = ctk.CTkEntry(f_add, width=100)
    ent_val.pack(side="left", padx=5)
    ctk.CTkLabel(f_add, text="Vencimento:").pack(side="left", padx=(10, 5))
    ent_venc = ctk.CTkEntry(f_add, width=110, placeholder_text="DD/MM/AAAA")
    ent_venc.pack(side="left", padx=5)
    
    f_filtros = ctk.CTkFrame(tab, fg_color="transparent")
    f_filtros.pack(fill="x", padx=20, pady=(20, 10))
    ctk.CTkLabel(f_filtros, text="Status:").pack(side="left", padx=(0, 5))
    cb_status = ctk.CTkComboBox(f_filtros, values=["Todas Pendentes", "Vencidas", "A Vencer Hoje", "A Vencer", "Todas (Inclui Pagas)"], width=180)
    cb_status.pack(side="left", padx=5)
    ctk.CTkLabel(f_filtros, text="Buscar:").pack(side="left", padx=(10, 5))
    ent_busca = ctk.CTkEntry(f_filtros, placeholder_text="Descrição...", width=150)
    ent_busca.pack(side="left", padx=5)
    ctk.CTkLabel(f_filtros, text="De:").pack(side="left", padx=(10, 5))
    ent_d_ini = ctk.CTkEntry(f_filtros, width=100, placeholder_text="DD/MM/AAAA")
    ent_d_ini.pack(side="left", padx=5)
    ctk.CTkLabel(f_filtros, text="Até:").pack(side="left", padx=5)
    ent_d_fim = ctk.CTkEntry(f_filtros, width=100, placeholder_text="DD/MM/AAAA")
    ent_d_fim.pack(side="left", padx=5)
    
    frame_lista = ctk.CTkScrollableFrame(tab, fg_color="#1e1e1e")
    frame_lista.pack(fill="both", expand=True, padx=20, pady=10)

    def salvar_conta():
        d = ent_desc.get().strip()
        v_str = ent_val.get().strip()
        dt_str = ent_venc.get().strip()
        if not d or not v_str or not dt_str:
            messagebox.showerror("Erro", "Preencha todos os campos!")
            return
        try: v = float(v_str.replace(",", "."))
        except ValueError:
            messagebox.showerror("Erro", "Valor numérico inválido!")
            return
        try: dt_db = datetime.strptime(dt_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Erro", "Data de vencimento inválida! Use DD/MM/AAAA.")
            return
            
        conn = conectar()
        conn.execute("INSERT INTO contas_pagar (descricao, valor, data_vencimento, status) VALUES (?, ?, ?, 'Pendente')", (d, v, dt_db))
        conn.commit()
        conn.close()
        registrar_log(usuario_logado, f"Cadastrou a conta a pagar: '{d}' no valor de R$ {v:.2f}")
        ent_desc.delete(0, 'end')
        ent_val.delete(0, 'end')
        ent_venc.delete(0, 'end')
        atualizar_lista()
        messagebox.showinfo("Sucesso", "Conta a pagar cadastrada com sucesso!")

    def limpar_filtros():
        cb_status.set("Todas Pendentes")
        ent_busca.delete(0, 'end')
        ent_d_ini.delete(0, 'end')
        ent_d_fim.delete(0, 'end')
        atualizar_lista()

    def atualizar_lista(*args):
        for w in frame_lista.winfo_children(): w.destroy()
        termo = ent_busca.get().strip()
        sf = cb_status.get()
        d_ini_str = ent_d_ini.get().strip()
        d_fim_str = ent_d_fim.get().strip()
        hoje = datetime.now().strftime("%Y-%m-%d")
        query = "SELECT id, descricao, valor, data_vencimento, status, data_pagamento FROM contas_pagar WHERE descricao LIKE ? "
        params = [f"%{termo}%"]

        if sf == "Todas Pendentes": query += " AND status = 'Pendente' "
        elif sf == "Vencidas": query += " AND status = 'Pendente' AND data_vencimento < ? "; params.append(hoje)
        elif sf == "A Vencer Hoje": query += " AND status = 'Pendente' AND data_vencimento = ? "; params.append(hoje)
        elif sf == "A Vencer": query += " AND status = 'Pendente' AND data_vencimento > ? "; params.append(hoje)

        if len(d_ini_str) == 10 and len(d_fim_str) == 10:
            try:
                d_ini_db = datetime.strptime(d_ini_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                d_fim_db = datetime.strptime(d_fim_str, "%d/%m/%Y").strftime("%Y-%m-%d")
                query += " AND data_vencimento BETWEEN ? AND ? "
                params.extend([d_ini_db, d_fim_db])
            except: pass
                
        query += " ORDER BY status DESC, data_vencimento ASC"

        conn = conectar()
        contas = conn.execute(query, params).fetchall()
        conn.close()

        f_cabecalho = ctk.CTkFrame(frame_lista, fg_color="transparent")
        f_cabecalho.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(f_cabecalho, text="ID", width=50, anchor="center", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="DESCRIÇÃO / BOLETO", width=350, anchor="w", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="VALOR", width=100, anchor="e", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="VENCIMENTO", width=100, anchor="center", font=("Arial", 12, "bold")).pack(side="left", padx=5)
        ctk.CTkLabel(f_cabecalho, text="STATUS", width=80, anchor="center", font=("Arial", 12, "bold")).pack(side="left", padx=5)

        for p in contas:
            f_item = ctk.CTkFrame(frame_lista)
            f_item.pack(fill="x", pady=2)
            ctk.CTkLabel(f_item, text=f"#{p[0]}", width=50, anchor="center").pack(side="left", padx=5)
            ctk.CTkLabel(f_item, text=f"{p[1][:40]}", width=350, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(f_item, text=f"R$ {p[2]:.2f}", width=100, anchor="e").pack(side="left", padx=5)
            
            try: d_br = datetime.strptime(p[3], "%Y-%m-%d").strftime("%d/%m/%Y")
            except: d_br = p[3]
                
            c_data = "white"
            if p[4] == "Pendente":
                if p[3] < hoje: c_data = "#e74c3c" 
                elif p[3] == hoje: c_data = "#f1c40f" 
                
            ctk.CTkLabel(f_item, text=d_br, width=100, text_color=c_data).pack(side="left", padx=5)
            c_stat = "#e74c3c" if p[4] == "Pendente" else "#2ecc71"
            ctk.CTkLabel(f_item, text=p[4], width=80, text_color=c_stat, font=("Arial", 12, "bold")).pack(side="left", padx=5)

            if p[4] == "Pendente":
                btn_pagar = ctk.CTkButton(f_item, text="💰 PAGAR", width=90, fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 11, "bold"), command=lambda pid=p[0]: pagar(pid))
                btn_pagar.pack(side="right", padx=5)
                btn_adiar = ctk.CTkButton(f_item, text="📅 ADIAR", width=90, fg_color="#f39c12", hover_color="#e67e22", text_color="black", font=("Arial", 11, "bold"), command=lambda pid=p[0]: adiar(pid))
                btn_adiar.pack(side="right", padx=5)
            else:
                btn_cancelar = ctk.CTkButton(f_item, text="↩️ CANCELAR", width=90, fg_color="#c0392b", hover_color="#e74c3c", text_color="white", font=("Arial", 11, "bold"), command=lambda pid=p[0]: estornar(pid))
                btn_cancelar.pack(side="right", padx=5)
                
            btn_excluir = ctk.CTkButton(f_item, text="❌ EXCLUIR", width=90, fg_color="#c0392b", hover_color="#e74c3c", font=("Arial", 11, "bold"), command=lambda pid=p[0]: excluir(pid))
            btn_excluir.pack(side="right", padx=5)

    def adiar(pid):
        dialog = ctk.CTkInputDialog(text="Nova data de vencimento\nFormato: DD/MM/AAAA", title="Adiar Conta")
        d = dialog.get_input()
        if d:
            try:
                data_db = datetime.strptime(d, "%d/%m/%Y").strftime("%Y-%m-%d")
                conn = conectar()
                conn.execute("UPDATE contas_pagar SET data_vencimento=? WHERE id=?", (data_db, pid))
                conn.commit()
                conn.close()
                registrar_log(usuario_logado, f"Adiou o vencimento da Conta a Pagar #{pid} para {d}")
                atualizar_lista()
            except: messagebox.showerror("Erro", "Formato inválido. Use DD/MM/AAAA.")

    def pagar(pid):
        if messagebox.askyesno("Confirmação", "Confirmar pagamento desta conta?"):
            conn = conectar()
            conn.execute("UPDATE contas_pagar SET status='Pago', data_pagamento=? WHERE id=?", (datetime.now().strftime("%Y-%m-%d"), pid))
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, f"Deu baixa/pagou a Conta #{pid}")
            atualizar_lista()
            
    def estornar(pid):
        if messagebox.askyesno("Cancelar Pagamento", "Deseja reverter este pagamento para Pendente?"):
            conn = conectar()
            conn.execute("UPDATE contas_pagar SET status='Pendente', data_pagamento=NULL WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, f"Estornou o pagamento da Conta #{pid}")
            atualizar_lista()
            
    def excluir(pid):
        if messagebox.askyesno("Cuidado", "Deseja excluir esta conta permanentemente?"):
            conn = conectar()
            conn.execute("DELETE FROM contas_pagar WHERE id=?", (pid,))
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, f"Excluiu a Conta a Pagar #{pid}")
            atualizar_lista()

    btn_add_conta = ctk.CTkButton(f_add, text="➕ CADASTRAR", fg_color="green", command=salvar_conta)
    btn_add_conta.pack(side="left", padx=15)
    btn_limpar_f = ctk.CTkButton(f_filtros, text="Limpar Filtros", fg_color="gray", width=100, command=limpar_filtros)
    btn_limpar_f.pack(side="left", padx=10)
    cb_status.configure(command=atualizar_lista)
    ent_busca.bind("<KeyRelease>", atualizar_lista)
    ent_d_ini.bind("<KeyRelease>", atualizar_lista)
    ent_d_fim.bind("<KeyRelease>", atualizar_lista)
    atualizar_lista()


# =========================================================
# ABA: HISTÓRICO
# =========================================================
def render_aba_historico(tab, usuario_logado, cargo_usuario):
    ctk.CTkLabel(tab, text="HISTÓRICO E EXTRATO DE CLIENTES", font=("Arial", 20, "bold")).pack(pady=10)
    f_b = ctk.CTkFrame(tab)
    f_b.pack(fill="x", padx=20, pady=10)
    ctk.CTkLabel(f_b, text="Buscar Cliente:").pack(side="left", padx=(0, 5))
    ent_busca = ctk.CTkEntry(f_b, placeholder_text="Nome...", width=200)
    ent_busca.pack(side="left", padx=5)
    cb_cliente = ctk.CTkComboBox(f_b, values=["Selecione"], width=300)
    cb_cliente.pack(side="left", padx=10)
    btn_gerar = ctk.CTkButton(f_b, text="GERAR EXTRATO", fg_color="#16a085", hover_color="#1abc9c", command=lambda: gerar_extrato())
    btn_gerar.pack(side="left", padx=10)
    txt_hist = ctk.CTkTextbox(tab, font=("Courier New", 14))
    txt_hist.pack(fill="both", expand=True, padx=20, pady=(10, 5))
    f_det = ctk.CTkFrame(tab, fg_color="transparent")
    f_det.pack(fill="x", padx=20, pady=(5, 10))
    ctk.CTkLabel(f_det, text="Ver Detalhes do Pedido - ID:").pack(side="left", padx=(0, 5))
    ent_detalhe = ctk.CTkEntry(f_det, width=80)
    ent_detalhe.pack(side="left", padx=5)

    def filtrar_cliente(*args):
        f = ent_busca.get()
        conn = conectar()
        clis = conn.execute("SELECT id, nome FROM clientes WHERE nome LIKE ?", (f"%{f}%",)).fetchall()
        conn.close()
        lista = [f"{c[0]} - {c[1]}" for c in clis] if clis else ["Nenhum"]
        cb_cliente.configure(values=lista)
        cb_cliente.set(lista[0])

    def gerar_extrato():
        txt_hist.delete("1.0", "end")
        sel = cb_cliente.get()
        if not sel or sel in ["Nenhum", "Selecione"]: return
        cid, nome = sel.split(" - ", 1)
        conn = conectar()
        vendas = conn.execute("SELECT id, data_hora, valor_total, forma_pagto, status FROM vendas WHERE cliente_id=? AND status != 'Orcamento' ORDER BY id DESC", (cid,)).fetchall()
        pend = conn.execute("SELECT valor FROM parcelas p JOIN vendas v ON p.venda_id=v.id WHERE v.cliente_id=? AND p.status='Pendente'", (cid,)).fetchall()
        conn.close()
        t_comp = sum(v[2] for v in vendas)
        t_pend = sum(p[0] for p in pend)
        txt_hist.insert("end", f"EXTRATO - Cliente: {nome}\n{'='*85}\n💰 COMPRADO: R$ {t_comp:.2f}  |  ⚠️ DÍVIDA: R$ {t_pend:.2f}\n{'='*85}\n\n{'ID':<5} | {'DATA':<20} | {'VALOR':<12} | {'PAGTO':<12} | {'STATUS'}\n{'-'*85}\n")
        for v in vendas:
            try: d_venda = datetime.strptime(v[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
            except: d_venda = v[1][:16]
            txt_hist.insert("end", f"#{v[0]:<4} | {d_venda:<20} | R$ {v[2]:<9.2f} | {v[3]:<12} | {v[4]}\n")

    def ver_detalhes(*args):
        vid = ent_detalhe.get().strip()
        if not vid: return
        conn = conectar()
        venda = conn.execute("SELECT v.data_hora, v.valor_total, c.nome, v.forma_pagto, v.status FROM vendas v LEFT JOIN clientes c ON v.cliente_id = c.id WHERE v.id=?", (vid,)).fetchone()
        if not venda:
            messagebox.showerror("Erro", "Venda/Orçamento não encontrado.")
            conn.close(); return
        itens = conn.execute("SELECT nome_produto, preco, quantidade FROM itens_venda WHERE venda_id=?", (vid,)).fetchall()
        parcelas = conn.execute("SELECT numero_parcela, valor, data_vencimento, data_pagamento, status FROM parcelas WHERE venda_id=? ORDER BY numero_parcela ASC", (vid,)).fetchall()
        conn.close()
        txt_hist.delete("1.0", "end")
        try: d_venda = datetime.strptime(venda[0], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
        except: d_venda = venda[0][:16]
        
        tipo_doc = "ORÇAMENTO" if venda[4] == "Orcamento" else "VENDA"
        txt_hist.insert("end", f"{tipo_doc} #{vid} - {venda[2]}\nData: {d_venda} | Pagto: {venda[3]} | Total: R$ {venda[1]:.2f}\nStatus: {venda[4]}\n{'='*85}\n📦 PRODUTOS:\n")
        for i in itens:
            qtd = i[2] if len(i)>2 and i[2] is not None else 1
            txt_hist.insert("end", f" -> {qtd:02d}x {i[0]:<50} | R$ {i[1]:.2f}\n")
            
        if venda[4] != "Orcamento":
            txt_hist.insert("end", f"\n💳 PARCELAS:\n")
            if not parcelas: txt_hist.insert("end", " -> Pagamento à vista.\n")
            else:
                for p in parcelas:
                    try: dbr = datetime.strptime(p[2], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except: dbr = p[2]
                    inf = f"(Pago em: {p[3]})" if p[4] == 'Pago' else ""
                    txt_hist.insert("end", f" -> {p[0]}x | R$ {p[1]:>8.2f} | Venc: {dbr} | {p[4]:<8} {inf}\n")
        ent_detalhe.delete(0, 'end')

    ent_busca.bind("<KeyRelease>", filtrar_cliente)
    ent_detalhe.bind("<Return>", ver_detalhes)
    btn_det = ctk.CTkButton(f_det, text="VER DETALHES", fg_color="#f39c12", text_color="black", font=("Arial", 12, "bold"), command=ver_detalhes)
    btn_det.pack(side="left", padx=10)


# =========================================================
# ABA: RELATÓRIOS E ANÁLISES (COM BALANÇO DE ESTOQUE)
# =========================================================
def render_aba_relatorios(tab, usuario_logado, cargo_usuario, liberar_pagar):
    f_linha1 = ctk.CTkFrame(tab, fg_color="transparent")
    f_linha1.pack(fill="x", padx=20, pady=5)
    
    ctk.CTkLabel(f_linha1, text="Período de:").pack(side="left", padx=(0, 5))
    ent_ini = ctk.CTkEntry(f_linha1, width=110, placeholder_text="DD/MM/AAAA")
    ent_ini.pack(side="left", padx=5)
    ent_ini.insert(0, datetime.now().strftime("%d/%m/%Y"))
    
    ctk.CTkLabel(f_linha1, text="até").pack(side="left", padx=5)
    ent_fim = ctk.CTkEntry(f_linha1, width=110, placeholder_text="DD/MM/AAAA")
    ent_fim.pack(side="left", padx=5)
    ent_fim.insert(0, datetime.now().strftime("%d/%m/%Y"))

    f_linha2 = ctk.CTkFrame(tab, fg_color="transparent")
    f_linha2.pack(fill="x", padx=20, pady=5)
    
    ctk.CTkLabel(f_linha2, text="Tipo:").pack(side="left", padx=(0, 5))
    lbl_status = ctk.CTkLabel(f_linha2, text="Filtro:")
    cb_status = ctk.CTkComboBox(f_linha2, values=["Resumo Geral", "Apenas Entradas", "Apenas Saídas"], width=150)
    
    def ao_mudar_tipo(escolha):
        if escolha == "Fluxo de Caixa (Realizado)":
            cb_status.configure(values=["Resumo Geral", "Apenas Entradas", "Apenas Saídas"])
            cb_status.set("Resumo Geral")
            lbl_status.configure(text="Filtro:")
        elif escolha == "Balanço de Estoque (Posição Atual)":
            cb_status.configure(values=["Todos", "Estoque Positivo", "Estoque Zerado/Negativo"])
            cb_status.set("Todos")
            lbl_status.configure(text="Estoque:")
        else:
            cb_status.configure(values=["Todas", "Pagas", "Pendentes", "Vencidas", "A Vencer"])
            cb_status.set("Todas")
            lbl_status.configure(text="Status:")

    opcoes_tipo = ["Fluxo de Caixa (Realizado)", "Contas a Receber"]
    if liberar_pagar == 1 or cargo_usuario == "Desenvolvedor":
        opcoes_tipo.append("Contas a Pagar")
    opcoes_tipo.append("Balanço de Estoque (Posição Atual)")

    cb_tipo = ctk.CTkComboBox(f_linha2, values=opcoes_tipo, width=250, command=ao_mudar_tipo)
    cb_tipo.pack(side="left", padx=5)
    
    lbl_status.pack(side="left", padx=(10, 5))
    cb_status.pack(side="left", padx=5)

    btn_rel_tela = ctk.CTkButton(f_linha2, text="📊 GERAR RELATÓRIO", fg_color="#2980b9", hover_color="#3498db", command=lambda: gerar_relatorio_tela())
    btn_rel_tela.pack(side="left", padx=15)
    
    btn_rel_pdf = ctk.CTkButton(f_linha2, text="🖨️ GERAR PDF", fg_color="#27ae60", hover_color="#2ecc71", command=lambda: gerar_relatorio_pdf())
    btn_rel_pdf.pack(side="left", padx=5)

    txt_rel = ctk.CTkTextbox(tab, font=("Courier New", 14))
    txt_rel.pack(fill="both", expand=True, padx=20, pady=(5, 10))

    f_linha3 = ctk.CTkFrame(tab, fg_color="transparent")
    f_linha3.pack(fill="x", padx=20, pady=(0, 15))
    
    ctk.CTkLabel(f_linha3, text="Produto:").pack(side="left", padx=(0, 5))
    ent_busca_prod = ctk.CTkEntry(f_linha3, width=250, placeholder_text="Nome do Produto...")
    ent_busca_prod.pack(side="left", padx=5)
    
    btn_hist = ctk.CTkButton(f_linha3, text="🔎 HISTÓRICO DO PRODUTO", fg_color="#8e44ad", hover_color="#9b59b6", command=lambda: hist_produto())
    btn_hist.pack(side="left", padx=10)
    
    btn_rank = ctk.CTkButton(f_linha3, text="🔝 MAIS VENDIDOS", text_color="black", fg_color="#e67e22", hover_color="#d35400", command=lambda: relatorio_produtos())
    btn_rank.pack(side="left", padx=15)

    def obter_datas():
        i_str = ent_ini.get().strip()
        f_str = ent_fim.get().strip()
        try:
            d1 = datetime.strptime(i_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            d2 = datetime.strptime(f_str, "%d/%m/%Y").strftime("%Y-%m-%d")
            return d1, d2, i_str, f_str
        except:
            return None, None, None, None

    def gerar_relatorio_tela():
        txt_rel.delete("1.0", "end")
        i_db, f_db, i_br, f_br = obter_datas()
        
        tipo = cb_tipo.get()
        status = cb_status.get()
        hoje = datetime.now().strftime("%Y-%m-%d")
        conn = conectar()

        if tipo == "Balanço de Estoque (Posição Atual)":
            query = "SELECT id, nome, estoque, preco_custo, preco FROM produtos WHERE 1=1"
            if status == "Estoque Positivo":
                query += " AND estoque > 0"
            elif status == "Estoque Zerado/Negativo":
                query += " AND estoque <= 0"
            query += " ORDER BY nome ASC"

            dados = conn.execute(query).fetchall()
            
            txt_rel.insert("end", f"RELATÓRIO: BALANÇO DE ESTOQUE (POSIÇÃO ATUAL)\nStatus: {status}\n{'='*80}\n")
            txt_rel.insert("end", f"{'ID':<5} | {'PRODUTO':<30} | {'ESTOQUE':<8} | {'CUSTO UN.':<10} | {'VENDA UN.'}\n{'-'*80}\n")

            tot_custo = 0
            tot_venda = 0
            for d in dados:
                est = d[2]
                custo_un = d[3] if d[3] is not None else 0.0
                venda_un = d[4] if d[4] is not None else 0.0
                
                if est > 0:
                    tot_custo += (est * custo_un)
                    tot_venda += (est * venda_un)

                txt_rel.insert("end", f"#{d[0]:<4} | {d[1][:30]:<30} | {est:<8} | R$ {custo_un:<7.2f} | R$ {venda_un:.2f}\n")

            lucro_potencial = tot_venda - tot_custo
            txt_rel.insert("end", f"{'-'*80}\n")
            txt_rel.insert("end", f"RESUMO FINANCEIRO (APENAS ESTOQUE POSITIVO):\n")
            txt_rel.insert("end", f"CUSTO TOTAL IMOBILIZADO:     R$ {tot_custo:.2f}\n")
            txt_rel.insert("end", f"VALOR TOTAL DE VENDA:        R$ {tot_venda:.2f}\n")
            txt_rel.insert("end", f"LUCRO BRUTO POTENCIAL:       R$ {lucro_potencial:.2f}\n")

        elif tipo == "Fluxo de Caixa (Realizado)":
            if not i_db: return messagebox.showerror("Erro", "Formato de data inválido. Use DD/MM/AAAA")
            
            v_vista = conn.execute("SELECT v.id, v.data_hora, v.valor_total, v.forma_pagto, c.nome FROM vendas v LEFT JOIN clientes c ON v.cliente_id=c.id WHERE date(v.data_hora) BETWEEN ? AND ? AND v.forma_pagto != 'A Prazo' AND v.status NOT IN ('Cancelado', 'Orcamento') ORDER BY v.id DESC", (i_db, f_db)).fetchall()
            p_pagas = conn.execute("SELECT p.venda_id, p.numero_parcela, p.valor, p.data_pagamento, c.nome FROM parcelas p JOIN vendas v ON p.venda_id=v.id LEFT JOIN clientes c ON v.cliente_id=c.id WHERE p.status='Pago' AND p.data_pagamento BETWEEN ? AND ? ORDER BY p.data_pagamento DESC", (i_db, f_db)).fetchall()
            c_pagas = conn.execute("SELECT id, descricao, valor, data_pagamento FROM contas_pagar WHERE status='Pago' AND data_pagamento BETWEEN ? AND ? ORDER BY data_pagamento DESC", (i_db, f_db)).fetchall()
            
            t_vista = sum(v[2] for v in v_vista)
            t_parc = sum(p[2] for p in p_pagas)
            t_entradas = t_vista + t_parc
            t_saidas = sum(c[2] for c in c_pagas)
            saldo = t_entradas - t_saidas
            
            txt_rel.insert("end", f"RELATÓRIO: FLUXO DE CAIXA REALIZADO\nPeríodo: {i_br} até {f_br}\n{'='*80}\n")
            
            if status in ["Resumo Geral", "Apenas Entradas"]:
                txt_rel.insert("end", f"🟢 ENTRADAS À VISTA (Dinheiro, Pix, Cartões): R$ {t_vista:>10.2f}\n")
                txt_rel.insert("end", f"🟢 RECEBIMENTOS DE DÍVIDAS (Parcelas Pagas): R$ {t_parc:>10.2f}\n")
                txt_rel.insert("end", f"   TOTAL DE ENTRADAS NO PERÍODO:             R$ {t_entradas:>10.2f}\n{'-'*80}\n")
            
            if status in ["Resumo Geral", "Apenas Saídas"]:
                txt_rel.insert("end", f"🔴 SAÍDAS (Contas a Pagar Liquidadas):       R$ {t_saidas:>10.2f}\n{'-'*80}\n")
                
            if status == "Resumo Geral":
                txt_rel.insert("end", f"💰 SALDO LÍQUIDO DO CAIXA:                   R$ {saldo:>10.2f}\n{'='*80}\n\n")
            
            if status in ["Resumo Geral", "Apenas Entradas"]:
                txt_rel.insert("end", "DETALHAMENTO DE ENTRADAS À VISTA:\n")
                for v in v_vista:
                    try: dv = datetime.strptime(v[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m %H:%M")
                    except: dv = v[1][:11]
                    txt_rel.insert("end", f" -> Venda #{v[0]:<4} | {dv:<13} | {v[3]:<10} | R$ {v[2]:>8.2f} | {(v[4] or 'Consumidor')[:15]}\n")
                    
                txt_rel.insert("end", f"\nDETALHAMENTO DE PARCELAS RECEBIDAS:\n")
                for p in p_pagas:
                    try: dp = datetime.strptime(p[3], "%Y-%m-%d").strftime("%d/%m")
                    except: dp = p[3][:5]
                    txt_rel.insert("end", f" -> Parcela {p[1]}x da Venda #{p[0]:<4} | Pago: {dp} | R$ {p[2]:>8.2f} | {(p[4] or 'Consumidor')[:15]}\n")
            
            if status in ["Resumo Geral", "Apenas Saídas"]:
                txt_rel.insert("end", f"\n{'-'*80}\nDETALHAMENTO DE CONTAS PAGAS:\n")
                for c in c_pagas:
                    try: dc = datetime.strptime(c[3], "%Y-%m-%d").strftime("%d/%m")
                    except: dc = c[3][:5]
                    txt_rel.insert("end", f" -> Boleto #{c[0]:<4} | Pago: {dc} | R$ {c[2]:>8.2f} | {c[1][:30]}\n")

        elif tipo == "Contas a Receber":
            if not i_db: return messagebox.showerror("Erro", "Formato de data inválido.")
            query = "SELECT p.id, p.venda_id, p.numero_parcela, c.nome, p.valor, p.data_vencimento, p.status, p.data_pagamento FROM parcelas p JOIN vendas v ON p.venda_id = v.id JOIN clientes c ON v.cliente_id = c.id WHERE p.status != 'Cancelado'"
            params = []
            
            if status == "Pagas":
                query += " AND p.status = 'Pago' AND p.data_pagamento BETWEEN ? AND ?"
                params.extend([i_db, f_db])
            else:
                query += " AND p.data_vencimento BETWEEN ? AND ?"
                params.extend([i_db, f_db])
                if status == "Pendentes": query += " AND p.status = 'Pendente'"
                elif status == "Vencidas": query += " AND p.status = 'Pendente' AND p.data_vencimento < ?"; params.append(hoje)
                elif status == "A Vencer": query += " AND p.status = 'Pendente' AND p.data_vencimento >= ?"; params.append(hoje)

            query += " ORDER BY p.data_vencimento ASC"
            dados = conn.execute(query, params).fetchall()
            
            txt_rel.insert("end", f"RELATÓRIO: CONTAS A RECEBER ({status.upper()})\nPeríodo: {i_br} a {f_br}\n{'='*80}\n")
            tot = 0
            for d in dados:
                tot += d[4]
                try: dt_venc = datetime.strptime(d[5], "%Y-%m-%d").strftime("%d/%m/%Y") if d[5] else ""
                except: dt_venc = d[5]
                txt_rel.insert("end", f" Venda #{d[1]:<4} | Parc {d[2]}x | Venc: {dt_venc} | R$ {d[4]:>8.2f} | Status: {d[6]:<9} | {(d[3] or 'Consumidor')[:15]}\n")
            txt_rel.insert("end", f"{'-'*80}\nTOTAL FILTRADO: R$ {tot:.2f}\n")

        elif tipo == "Contas a Pagar":
            if not i_db: return messagebox.showerror("Erro", "Formato de data inválido.")
            query = "SELECT id, descricao, valor, data_vencimento, status, data_pagamento FROM contas_pagar WHERE 1=1"
            params = []
            
            if status == "Pagas":
                query += " AND status = 'Pago' AND data_pagamento BETWEEN ? AND ?"
                params.extend([i_db, f_db])
            else:
                query += " AND data_vencimento BETWEEN ? AND ?"
                params.extend([i_db, f_db])
                if status == "Pendentes": query += " AND status = 'Pendente'"
                elif status == "Vencidas": query += " AND status = 'Pendente' AND data_vencimento < ?"; params.append(hoje)
                elif status == "A Vencer": query += " AND status = 'Pendente' AND data_vencimento >= ?"; params.append(hoje)

            query += " ORDER BY data_vencimento ASC"
            dados = conn.execute(query, params).fetchall()
            
            txt_rel.insert("end", f"RELATÓRIO: CONTAS A PAGAR ({status.upper()})\nPeríodo: {i_br} a {f_br}\n{'='*80}\n")
            tot = 0
            for d in dados:
                tot += d[2]
                try: dt_venc = datetime.strptime(d[3], "%Y-%m-%d").strftime("%d/%m/%Y") if d[3] else ""
                except: dt_venc = d[3]
                txt_rel.insert("end", f" Bol. #{d[0]:<4} | Venc: {dt_venc} | R$ {d[2]:>8.2f} | Status: {d[4]:<9} | {d[1][:25]}\n")
            txt_rel.insert("end", f"{'-'*80}\nTOTAL FILTRADO: R$ {tot:.2f}\n")

        conn.close()

    def gerar_relatorio_pdf():
        if not PDF_DISPONIVEL: return messagebox.showerror("Erro", "Biblioteca 'reportlab' não encontrada.")
            
        i_db, f_db, i_br, f_br = obter_datas()
        
        tipo = cb_tipo.get()
        status = cb_status.get()
        hoje = datetime.now().strftime("%Y-%m-%d")
        
        conn = conectar()
        emp = conn.execute("SELECT nome FROM empresa WHERE id=1").fetchone()
        nome_empresa = emp[0] if emp else "EMPRESA"
        pth = os.path.join(DIRETORIO_BASE, "recibos", f"relatorio_{datetime.now().strftime('%H%M%S')}.pdf")
        os.makedirs(os.path.dirname(pth), exist_ok=True)
        largura = 80 * mm

        if tipo == "Balanço de Estoque (Posição Atual)":
            query = "SELECT id, nome, estoque, preco_custo, preco FROM produtos WHERE 1=1"
            if status == "Estoque Positivo":
                query += " AND estoque > 0"
            elif status == "Estoque Zerado/Negativo":
                query += " AND estoque <= 0"
            query += " ORDER BY nome ASC"

            dados = conn.execute(query).fetchall()
            
            altura = (len(dados) + 30) * 4 * mm
            if altura < 100 * mm: altura = 100 * mm
            cnv = canvas.Canvas(pth, pagesize=(largura, altura))
            y = altura - (10 * mm)
            cnv.setFont("Helvetica-Bold", 10)
            cnv.drawCentredString(largura/2, y, nome_empresa)
            y -= 6 * mm
            cnv.setFont("Helvetica-Bold", 9)
            cnv.drawCentredString(largura/2, y, "BALANCO DE ESTOQUE")
            y -= 6 * mm
            cnv.setFont("Helvetica", 8)
            cnv.drawCentredString(largura/2, y, f"Filtro: {status}")
            y -= 8 * mm
            cnv.drawString(5 * mm, y, f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            y -= 5 * mm
            cnv.drawString(5 * mm, y, "-"*60)
            y -= 5 * mm
            
            tot_custo = 0
            tot_venda = 0
            cnv.setFont("Helvetica", 7)
            for d in dados:
                est = d[2]
                custo_un = d[3] if d[3] is not None else 0.0
                venda_un = d[4] if d[4] is not None else 0.0
                
                if est > 0:
                    tot_custo += (est * custo_un)
                    tot_venda += (est * venda_un)
                    
                cnv.drawString(5 * mm, y, f"#{d[0]} - {d[1][:20]} (Est: {est})")
                cnv.drawRightString(largura - 5*mm, y, f"V: R${venda_un:.2f} | C: R${custo_un:.2f}")
                y -= 4 * mm
                
            y -= 2 * mm
            cnv.setFont("Helvetica", 8)
            cnv.drawString(5 * mm, y, "-"*60)
            y -= 6 * mm
            cnv.setFont("Helvetica-Bold", 8)
            cnv.drawString(5 * mm, y, "RESUMO (ESTOQUE POSITIVO):")
            y -= 5 * mm
            cnv.setFont("Helvetica", 8)
            cnv.drawString(5 * mm, y, "Custo Total:")
            cnv.drawRightString(largura - 5*mm, y, f"R$ {tot_custo:.2f}")
            y -= 4 * mm
            cnv.drawString(5 * mm, y, "Venda Total:")
            cnv.drawRightString(largura - 5*mm, y, f"R$ {tot_venda:.2f}")
            y -= 4 * mm
            cnv.setFont("Helvetica-Bold", 9)
            cnv.drawString(5 * mm, y, "Lucro Potencial:")
            cnv.drawRightString(largura - 5*mm, y, f"R$ {tot_venda - tot_custo:.2f}")

        elif tipo == "Fluxo de Caixa (Realizado)":
            if not i_db: return messagebox.showerror("Erro", "Formato de data inválido.")
            v_vista = conn.execute("SELECT v.id, v.data_hora, v.valor_total, v.forma_pagto, c.nome FROM vendas v LEFT JOIN clientes c ON v.cliente_id=c.id WHERE date(v.data_hora) BETWEEN ? AND ? AND v.forma_pagto != 'A Prazo' AND v.status NOT IN ('Cancelado', 'Orcamento')", (i_db, f_db)).fetchall()
            p_pagas = conn.execute("SELECT p.venda_id, p.numero_parcela, p.valor, p.data_pagamento, c.nome FROM parcelas p JOIN vendas v ON p.venda_id=v.id LEFT JOIN clientes c ON v.cliente_id=c.id WHERE p.status='Pago' AND p.data_pagamento BETWEEN ? AND ?", (i_db, f_db)).fetchall()
            c_pagas = conn.execute("SELECT id, descricao, valor, data_pagamento FROM contas_pagar WHERE status='Pago' AND data_pagamento BETWEEN ? AND ?", (i_db, f_db)).fetchall()
            
            tot_entradas = sum(v[2] for v in v_vista) + sum(p[2] for p in p_pagas)
            tot_saidas = sum(c[2] for c in c_pagas)
            saldo = tot_entradas - tot_saidas
            
            altura = (len(v_vista) + len(p_pagas) + len(c_pagas) + 30) * 4 * mm
            if altura < 100 * mm: altura = 100 * mm
            cnv = canvas.Canvas(pth, pagesize=(largura, altura))
            y = altura - (10 * mm)
            
            cnv.setFont("Helvetica-Bold", 10)
            cnv.drawCentredString(largura/2, y, nome_empresa)
            y -= 6 * mm
            cnv.setFont("Helvetica-Bold", 9)
            cnv.drawCentredString(largura/2, y, "FLUXO DE CAIXA LÍQUIDO")
            y -= 8 * mm
            cnv.setFont("Helvetica", 8)
            cnv.drawString(5 * mm, y, f"Periodo: {i_br} a {f_br}")
            y -= 5 * mm
            cnv.drawString(5 * mm, y, "-"*60)
            y -= 5 * mm
            cnv.drawString(5 * mm, y, "Entradas Totais:")
            cnv.drawRightString(largura - 5*mm, y, f"R$ {tot_entradas:.2f}")
            y -= 5 * mm
            cnv.drawString(5 * mm, y, "Saidas (Contas Pagas):")
            cnv.drawRightString(largura - 5*mm, y, f"- R$ {tot_saidas:.2f}")
            y -= 5 * mm
            cnv.setFont("Helvetica-Bold", 10)
            cnv.drawString(5 * mm, y, "SALDO LIQUIDO:")
            cnv.drawRightString(largura - 5*mm, y, f"R$ {saldo:.2f}")
            y -= 8 * mm
            cnv.setFont("Helvetica", 8)
            cnv.drawString(5 * mm, y, "="*60)
            y -= 6 * mm
            
            if status in ["Resumo Geral", "Apenas Entradas"]:
                cnv.setFont("Helvetica-Bold", 8)
                cnv.drawString(5 * mm, y, "DETALHE DE ENTRADAS")
                y -= 6 * mm
                cnv.setFont("Helvetica", 7)
                for v in v_vista:
                    cnv.drawString(5 * mm, y, f"#{v[0]} - {(v[4] or 'Cons')[:10]}")
                    cnv.drawRightString(largura - 5*mm, y, f"R$ {v[2]:.2f}")
                    y -= 4 * mm
                for p in p_pagas:
                    cnv.drawString(5 * mm, y, f"Vnd#{p[0]} - P.{p[1]}x - {(p[4] or 'Cons')[:10]}")
                    cnv.drawRightString(largura - 5*mm, y, f"R$ {p[2]:.2f}")
                    y -= 4 * mm
                    
            if status in ["Resumo Geral", "Apenas Saídas"]:
                y -= 2 * mm
                cnv.setFont("Helvetica", 8)
                cnv.drawString(5 * mm, y, "-"*60)
                y -= 6 * mm
                cnv.setFont("Helvetica-Bold", 8)
                cnv.drawString(5 * mm, y, "DETALHE DE SAIDAS")
                y -= 6 * mm
                cnv.setFont("Helvetica", 7)
                for c in c_pagas:
                    cnv.drawString(5 * mm, y, f"Bol#{c[0]} - {c[1][:15]}")
                    cnv.drawRightString(largura - 5*mm, y, f"R$ {c[2]:.2f}")
                    y -= 4 * mm

        else:
            if not i_db: return messagebox.showerror("Erro", "Formato de data inválido.")
            query = ""; params = []
            if tipo == "Contas a Receber":
                query = "SELECT p.id, p.venda_id, p.numero_parcela, c.nome, p.valor, p.data_vencimento, p.status FROM parcelas p JOIN vendas v ON p.venda_id = v.id JOIN clientes c ON v.cliente_id = c.id WHERE p.status != 'Cancelado'"
                if status == "Pagas":
                    query += " AND p.status = 'Pago' AND p.data_pagamento BETWEEN ? AND ?"; params.extend([i_db, f_db])
                else:
                    query += " AND p.data_vencimento BETWEEN ? AND ?"; params.extend([i_db, f_db])
                    if status == "Pendentes": query += " AND p.status = 'Pendente'"
                    elif status == "Vencidas": query += " AND p.status = 'Pendente' AND p.data_vencimento < ?"; params.append(hoje)
                    elif status == "A Vencer": query += " AND p.status = 'Pendente' AND p.data_vencimento >= ?"; params.append(hoje)
            elif tipo == "Contas a Pagar":
                query = "SELECT id, descricao, valor, data_vencimento, status FROM contas_pagar WHERE 1=1"
                if status == "Pagas":
                    query += " AND status = 'Pago' AND data_pagamento BETWEEN ? AND ?"; params.extend([i_db, f_db])
                else:
                    query += " AND data_vencimento BETWEEN ? AND ?"; params.extend([i_db, f_db])
                    if status == "Pendentes": query += " AND status = 'Pendente'"
                    elif status == "Vencidas": query += " AND status = 'Pendente' AND data_vencimento < ?"; params.append(hoje)
                    elif status == "A Vencer": query += " AND status = 'Pendente' AND data_vencimento >= ?"; params.append(hoje)

            dados = conn.execute(query, params).fetchall()
            altura = (len(dados) + 20) * 4 * mm
            if altura < 100 * mm: altura = 100 * mm
            cnv = canvas.Canvas(pth, pagesize=(largura, altura))
            y = altura - (10 * mm)
            cnv.setFont("Helvetica-Bold", 10)
            cnv.drawCentredString(largura/2, y, nome_empresa)
            y -= 6 * mm
            cnv.setFont("Helvetica-Bold", 9)
            cnv.drawCentredString(largura/2, y, tipo.upper())
            y -= 6 * mm
            cnv.setFont("Helvetica", 8)
            cnv.drawCentredString(largura/2, y, f"Status: {status}")
            y -= 8 * mm
            cnv.drawString(5 * mm, y, f"Periodo: {i_br} a {f_br}")
            y -= 5 * mm
            cnv.drawString(5 * mm, y, "-"*60)
            y -= 6 * mm
            
            tot = 0
            cnv.setFont("Helvetica", 7)
            for d in dados:
                if tipo == "Contas a Receber":
                    tot += d[4]
                    cnv.drawString(5 * mm, y, f"Vnd#{d[1]} - P.{d[2]}x - {(d[3] or 'Cons')[:10]}")
                    cnv.drawRightString(largura - 5*mm, y, f"R$ {d[4]:.2f}")
                else:
                    tot += d[2]
                    cnv.drawString(5 * mm, y, f"Bol#{d[0]} - {d[1][:15]}")
                    cnv.drawRightString(largura - 5*mm, y, f"R$ {d[2]:.2f}")
                y -= 4 * mm
            
            y -= 2 * mm
            cnv.setFont("Helvetica", 8)
            cnv.drawString(5 * mm, y, "-"*60)
            y -= 6 * mm
            cnv.setFont("Helvetica-Bold", 10)
            cnv.drawString(5 * mm, y, "TOTAL FILTRADO:")
            cnv.drawRightString(largura - 5*mm, y, f"R$ {tot:.2f}")

        conn.close()
        cnv.save()
        os.startfile(os.path.abspath(pth))

    def relatorio_produtos():
        txt_rel.delete("1.0", "end")
        i_db, f_db, i_br, f_br = obter_datas()
        if not i_db: return messagebox.showerror("Erro", "Data inválida.")
            
        conn = conectar()
        query = "SELECT nome_produto, SUM(quantidade), SUM(preco) FROM itens_venda iv JOIN vendas v ON iv.venda_id = v.id WHERE date(v.data_hora) BETWEEN ? AND ? AND v.status NOT IN ('Cancelado', 'Orcamento') GROUP BY nome_produto ORDER BY SUM(quantidade) DESC LIMIT 30"
        ranking = conn.execute(query, (i_db, f_db)).fetchall()
        conn.close()

        txt_rel.insert("end", f"RANKING: PRODUTOS MAIS VENDIDOS ({i_br} até {f_br})\n{'='*80}\n")
        txt_rel.insert("end", f"{'POS':<4} | {'PRODUTO':<45} | {'QTD VENDIDA':<12} | {'ARRECADADO'}\n{'-'*80}\n")
        if not ranking: txt_rel.insert("end", "Nenhum produto vendido neste período.\n")
        for idx, r in enumerate(ranking):
            q = r[1] if r[1] is not None else 1
            txt_rel.insert("end", f"{idx+1:02d}º  | {r[0]:<45} | {q:<12} | R$ {r[2]:.2f}\n")

    def hist_produto():
        txt_rel.delete("1.0", "end")
        i_db, f_db, i_br, f_br = obter_datas()
        if not i_db: return
            
        termo = ent_busca_prod.get().strip()
        if not termo: return messagebox.showwarning("Aviso", "Digite o nome de um produto para buscar.")
            
        conn = conectar()
        query = "SELECT v.id, v.data_hora, iv.preco, c.nome, iv.quantidade FROM itens_venda iv JOIN vendas v ON iv.venda_id = v.id LEFT JOIN clientes c ON v.cliente_id = c.id WHERE iv.nome_produto LIKE ? AND date(v.data_hora) BETWEEN ? AND ? AND v.status NOT IN ('Cancelado', 'Orcamento') ORDER BY v.data_hora DESC"
        hist = conn.execute(query, (f"%{termo}%", i_db, f_db)).fetchall()
        conn.close()

        txt_rel.insert("end", f"HISTÓRICO DE VENDAS: '{termo}' ({i_br} a {f_br})\n{'='*80}\n")
        txt_rel.insert("end", f"{'RECIBO':<8} | {'QTD':<4} | {'DATA/HORA':<18} | {'VALOR COBRADO':<15} | {'CLIENTE'}\n{'-'*80}\n")
        
        if not hist: txt_rel.insert("end", "Nenhum registro encontrado neste período.\n")
            
        total_arr = 0; total_qtd = 0
        for h in hist:
            try: d_venda = datetime.strptime(h[1], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
            except: d_venda = h[1][:16]
            q = h[4] if len(h)>4 and h[4] is not None else 1
            total_qtd += q
            txt_rel.insert("end", f"#{h[0]:<6} | {q:02d}x  | {d_venda:<18} | R$ {h[2]:<12.2f} | {(h[3] or 'Consumidor')}\n")
            total_arr += h[2]
            
        txt_rel.insert("end", f"{'-'*80}\nQUANTIDADE TOTAL VENDIDA: {total_qtd}  |  VALOR TOTAL ARRECADADO: R$ {total_arr:.2f}")

    ent_busca_prod.bind("<Return>", lambda e: hist_produto())
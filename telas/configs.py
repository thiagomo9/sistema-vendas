import customtkinter as ctk
import os
import shutil
from datetime import datetime
from tkinter import messagebox, filedialog
from database import conectar, DB_PATH, registrar_log
from seguranca import ativar_licenca, verificar_licenca_db, NOME_DESENVOLVEDOR, TELEFONE_SUPORTE

def setup_configuracoes(container, usuario_logado, cargo_usuario):
    conn = conectar()
    conf = conn.execute("SELECT ver_dados_empresa, ver_usuarios, ver_permissoes, ver_auditoria FROM configuracoes WHERE id=1").fetchone()
    conn.close()
    
    lib_empresa = conf[0] if conf else 1
    lib_usuarios = conf[1] if conf else 1
    lib_permissoes = conf[2] if conf else 1
    lib_auditoria = conf[3] if conf else 1

    ctk.CTkLabel(container, text="PAINEL DE CONTROLE E CONFIGURAÇÕES", font=("Arial", 22, "bold")).pack(pady=10)
    
    tabview = ctk.CTkTabview(container)
    tabview.pack(fill="both", expand=True)
    
    tab_geral = tabview.add("🖥️ Visual e Backup")
    
    if lib_empresa == 1 or cargo_usuario == "Desenvolvedor":
        tab_empresa = tabview.add("🏢 Dados da Empresa")
        
    if cargo_usuario in ["Admin", "Desenvolvedor"]:
        if lib_usuarios == 1 or cargo_usuario == "Desenvolvedor":
            tab_usuarios = tabview.add("👥 Usuários")
        if lib_permissoes == 1 or cargo_usuario == "Desenvolvedor":
            tab_permissoes = tabview.add("🛡️ Permissões")
        if lib_auditoria == 1 or cargo_usuario == "Desenvolvedor":
            tab_logs = tabview.add("📜 Logs de Auditoria")
            
    if cargo_usuario == "Desenvolvedor":
        tab_dev = tabview.add("🔒 Licença & Status")
        tab_custom = tabview.add("🛠️ Customização")

    # =========================================================
    # ABA: VISUAL, DESCANSO DE TELA E BACKUP
    # =========================================================
    conn = conectar()
    conf_geral = conn.execute("SELECT tema, escala, ultimo_backup, auto_backup, descanso_tela, tempo_descanso FROM configuracoes WHERE id=1").fetchone()
    conn.close()
    
    f_v = ctk.CTkFrame(tab_geral, fg_color="transparent")
    f_v.pack(fill="x", padx=20, pady=10)
    
    bloco_tema = ctk.CTkFrame(f_v, fg_color="transparent")
    bloco_tema.pack(side="left", padx=10)
    ctk.CTkLabel(bloco_tema, text="Aparência (Tema):", font=("Arial", 12, "bold")).pack(anchor="w")
    
    def mudar_tema(t):
        ctk.set_appearance_mode(t)
        conn = conectar()
        conn.execute("UPDATE configuracoes SET tema=? WHERE id=1", (t,))
        conn.commit()
        conn.close()
        
    m_t = ctk.CTkOptionMenu(bloco_tema, values=["Dark", "Light"], command=mudar_tema)
    m_t.pack()
    m_t.set(conf_geral[0] if conf_geral else "Dark")
    
    bloco_escala = ctk.CTkFrame(f_v, fg_color="transparent")
    bloco_escala.pack(side="left", padx=20)
    ctk.CTkLabel(bloco_escala, text="Zoom da Interface:", font=("Arial", 12, "bold")).pack(anchor="w")
    
    def mudar_escala(e):
        v = float(e.replace("%", "")) / 100
        ctk.set_widget_scaling(v)
        ctk.set_window_scaling(v)
        conn = conectar()
        conn.execute("UPDATE configuracoes SET escala=? WHERE id=1", (e,))
        conn.commit()
        conn.close()
        
    m_e = ctk.CTkOptionMenu(bloco_escala, values=["80%","100%","120%","150%"], command=mudar_escala)
    m_e.pack()
    m_e.set(conf_geral[1] if conf_geral else "120%")

    ctk.CTkFrame(tab_geral, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=10)

    f_desc = ctk.CTkFrame(tab_geral, fg_color="transparent")
    f_desc.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(f_desc, text="Privacidade do Balcão:", font=("Arial", 14, "bold")).pack(side="left", padx=10)
    
    sw_descanso = ctk.CTkSwitch(f_desc, text="Ativar Descanso de Tela Automático")
    sw_descanso.pack(side="left", padx=20)
    if conf_geral and conf_geral[4] == 1:
        sw_descanso.select()
    
    ctk.CTkLabel(f_desc, text="Inatividade (Min):", font=("Arial", 12, "bold")).pack(side="left", padx=5)
    cb_tempo = ctk.CTkComboBox(f_desc, values=["1", "3", "5", "10", "15", "30"], width=80)
    cb_tempo.pack(side="left", padx=5)
    cb_tempo.set(str(conf_geral[5] if conf_geral else 5))
    
    def salvar_descanso():
        d = 1 if sw_descanso.get() else 0
        t = int(cb_tempo.get())
        conn = conectar()
        conn.execute("UPDATE configuracoes SET descanso_tela=?, tempo_descanso=? WHERE id=1", (d, t))
        conn.commit()
        conn.close()
        messagebox.showinfo("Sucesso", "Configuração de Descanso de Tela salva!\n(Terá efeito ao reiniciar o sistema)")

    ctk.CTkButton(f_desc, text="SALVAR TEMPO", fg_color="#2980b9", width=120, command=salvar_descanso).pack(side="left", padx=20)

    ctk.CTkFrame(tab_geral, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=10)

    f_bkp = ctk.CTkFrame(tab_geral, fg_color="transparent")
    f_bkp.pack(fill="x", padx=20, pady=10)
    
    ctk.CTkLabel(f_bkp, text="BACKUP DE SEGURANÇA MANUAL", font=("Arial", 16, "bold"), text_color="#2ecc71").pack(pady=(10, 5))
    
    ultimo_bkp = conf_geral[2] if conf_geral and conf_geral[2] else "Nunca realizado"
    lbl_backup_info = ctk.CTkLabel(f_bkp, text=f"Último backup: {ultimo_bkp}", font=("Arial", 14))
    lbl_backup_info.pack(pady=5)
    
    def fazer_backup():
        pasta_destino = filedialog.askdirectory(title="Selecione a pasta para salvar o backup")
        if pasta_destino:
            try:
                data_atual = datetime.now().strftime("%Y%m%d_%H%M%S")
                nome_arquivo = f"sistema_vendas_backup_{data_atual}.db"
                caminho_destino = os.path.join(pasta_destino, nome_arquivo)
                shutil.copy2(DB_PATH, caminho_destino)
                data_formatada = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
                conn = conectar()
                conn.execute("UPDATE configuracoes SET ultimo_backup=? WHERE id=1", (data_formatada,))
                conn.commit()
                conn.close()
                lbl_backup_info.configure(text=f"Último backup: {data_formatada}")
                registrar_log(usuario_logado, "Realizou um Backup Manual do Banco de Dados.")
                messagebox.showinfo("Sucesso", f"Backup realizado com sucesso!\n\nSalvo em:\n{caminho_destino}")
            except Exception as e:
                messagebox.showerror("Erro", f"Falha ao realizar o backup:\n{str(e)}")

    ctk.CTkButton(f_bkp, text="💾 REALIZAR BACKUP AGORA", fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 12, "bold"), command=fazer_backup).pack(pady=15)

    # =========================================================
    # ABA: DADOS DA EMPRESA
    # =========================================================
    if lib_empresa == 1 or cargo_usuario == "Desenvolvedor":
        conn = conectar()
        e = conn.execute("SELECT nome, cnpj, endereco, telefone FROM empresa WHERE id=1").fetchone()
        conn.close()

        f_e1 = ctk.CTkFrame(tab_empresa, fg_color="transparent")
        f_e1.pack(fill="x", padx=20, pady=15)
        
        bloco_emp_nome = ctk.CTkFrame(f_e1, fg_color="transparent")
        bloco_emp_nome.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(bloco_emp_nome, text="Nome da Empresa:", font=("Arial", 12, "bold")).pack(anchor="w")
        e_emp_nome = ctk.CTkEntry(bloco_emp_nome)
        e_emp_nome.pack(fill="x")
        if e: e_emp_nome.insert(0, e[0])
        
        bloco_emp_cnpj = ctk.CTkFrame(f_e1, fg_color="transparent")
        bloco_emp_cnpj.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(bloco_emp_cnpj, text="CNPJ / NIF:", font=("Arial", 12, "bold")).pack(anchor="w")
        e_emp_cnpj = ctk.CTkEntry(bloco_emp_cnpj)
        e_emp_cnpj.pack(fill="x")
        if e: e_emp_cnpj.insert(0, e[1])
        
        f_e2 = ctk.CTkFrame(tab_empresa, fg_color="transparent")
        f_e2.pack(fill="x", padx=20, pady=5)
        
        bloco_emp_end = ctk.CTkFrame(f_e2, fg_color="transparent")
        bloco_emp_end.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(bloco_emp_end, text="Endereço Completo:", font=("Arial", 12, "bold")).pack(anchor="w")
        e_emp_end = ctk.CTkEntry(bloco_emp_end)
        e_emp_end.pack(fill="x")
        if e: e_emp_end.insert(0, e[2])
        
        bloco_emp_tel = ctk.CTkFrame(f_e2, fg_color="transparent")
        bloco_emp_tel.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(bloco_emp_tel, text="Telefone de Contato:", font=("Arial", 12, "bold")).pack(anchor="w")
        e_emp_tel = ctk.CTkEntry(bloco_emp_tel)
        e_emp_tel.pack(fill="x")
        if e: e_emp_tel.insert(0, e[3])
        
        def salvar_dados_empresa():
            conn = conectar()
            conn.execute("UPDATE empresa SET nome=?, cnpj=?, endereco=?, telefone=? WHERE id=1", (e_emp_nome.get(), e_emp_cnpj.get(), e_emp_end.get(), e_emp_tel.get()))
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, "Atualizou os dados da empresa.")
            messagebox.showinfo("Ok", "Dados atualizados com sucesso!")

        ctk.CTkButton(tab_empresa, text="SALVAR DADOS DA EMPRESA", fg_color="#2980b9", command=salvar_dados_empresa).pack(pady=30)

    # =========================================================
    # ABA: USUÁRIOS
    # =========================================================
    if cargo_usuario in ["Admin", "Desenvolvedor"] and (lib_usuarios == 1 or cargo_usuario == "Desenvolvedor"):
        f_master_u = ctk.CTkFrame(tab_usuarios, fg_color="transparent")
        f_master_u.pack(fill="x", padx=10, pady=10)
        
        lbl_modo_user = ctk.CTkLabel(f_master_u, text="NOVO CADASTRO DE USUÁRIO", font=("Arial", 18, "bold"), text_color="#3498db")
        lbl_modo_user.pack(pady=(0, 15))
        
        f_linha_u = ctk.CTkFrame(f_master_u, fg_color="transparent")
        f_linha_u.pack(fill="x", padx=20, pady=5)

        bloco_uid = ctk.CTkFrame(f_linha_u, fg_color="transparent")
        bloco_uid.pack(side="left", padx=10)
        ctk.CTkLabel(bloco_uid, text="ID:", font=("Arial", 12, "bold")).pack(anchor="w")
        u_id = ctk.CTkEntry(bloco_uid, width=60, state="readonly", fg_color="#2c3e50")
        u_id.pack(fill="x")

        bloco_unome = ctk.CTkFrame(f_linha_u, fg_color="transparent")
        bloco_unome.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(bloco_unome, text="Nome de Usuário (Login):", font=("Arial", 12, "bold")).pack(anchor="w")
        u_nome = ctk.CTkEntry(bloco_unome)
        u_nome.pack(fill="x")

        bloco_usenha = ctk.CTkFrame(f_linha_u, fg_color="transparent")
        bloco_usenha.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(bloco_usenha, text="Senha:", font=("Arial", 12, "bold")).pack(anchor="w")
        u_senha = ctk.CTkEntry(bloco_usenha, show="*")
        u_senha.pack(fill="x")
        
        bloco_ucargo = ctk.CTkFrame(f_linha_u, fg_color="transparent")
        bloco_ucargo.pack(side="left", padx=10, fill="x", expand=True)
        ctk.CTkLabel(bloco_ucargo, text="Nível de Acesso (Cargo):", font=("Arial", 12, "bold")).pack(anchor="w")
        
        cargos_permitidos = ["Caixa", "Gerente"]
        if cargo_usuario == "Desenvolvedor":
            cargos_permitidos.append("Admin")
            cargos_permitidos.append("Desenvolvedor")
            
        u_cargo = ctk.CTkComboBox(bloco_ucargo, values=cargos_permitidos)
        u_cargo.pack(fill="x")
        
        f_btns_u = ctk.CTkFrame(f_master_u, fg_color="transparent")
        f_btns_u.pack(pady=20)
        
        btn_salvar_u = ctk.CTkButton(f_btns_u, text="💾 GRAVAR DADOS", fg_color="green", hover_color="#27ae60", height=40)
        btn_salvar_u.pack(side="left", padx=10)
        
        btn_cancelar_u = ctk.CTkButton(f_btns_u, text="✖ CANCELAR EDIÇÃO", fg_color="#c0392b", hover_color="#e74c3c", height=40)

        ctk.CTkFrame(tab_usuarios, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=5)

        frame_lista_u = ctk.CTkScrollableFrame(tab_usuarios, fg_color="#1e1e1e")
        frame_lista_u.pack(fill="both", expand=True, padx=20, pady=10)

        def atualizar_usuarios():
            for w in frame_lista_u.winfo_children():
                w.destroy()
            
            conn = conectar()
            users = conn.execute("SELECT id, username, role, password FROM usuarios ORDER BY id ASC").fetchall()
            conn.close()
            
            for u in users:
                item = ctk.CTkFrame(frame_lista_u)
                item.pack(fill="x", pady=2)
                
                ctk.CTkLabel(item, text=f"ID: {u[0]}", width=60).pack(side="left", padx=5)
                ctk.CTkLabel(item, text=f"Login: {u[1]}", width=250, anchor="w").pack(side="left", padx=5)
                ctk.CTkLabel(item, text=f"Cargo: {u[2]}", width=150).pack(side="left", padx=5)
                
                pode_editar = True
                if u[2] == "Desenvolvedor" and cargo_usuario != "Desenvolvedor":
                    pode_editar = False
                
                if pode_editar:
                    btn_excluir = ctk.CTkButton(item, text="❌ EXCLUIR", width=80, fg_color="#c0392b", hover_color="#e74c3c", command=lambda uid=u[0]: u_excluir(uid))
                    btn_excluir.pack(side="right", padx=5)
                    btn_editar = ctk.CTkButton(item, text="✏️ EDITAR", width=80, fg_color="#f39c12", text_color="black", command=lambda user=u: carregar_u(user))
                    btn_editar.pack(side="right", padx=5)
                else:
                    ctk.CTkLabel(item, text="(Conta Protegida)", text_color="gray").pack(side="right", padx=15)

        def carregar_u(user):
            u_id.configure(state="normal")
            u_id.delete(0, 'end')
            u_id.insert(0, user[0])
            u_id.configure(state="readonly")
            u_nome.delete(0, 'end')
            u_nome.insert(0, user[1])
            u_cargo.set(user[2])
            u_senha.delete(0, 'end')
            u_senha.insert(0, user[3])
            
            lbl_modo_user.configure(text="📝 MODO DE EDIÇÃO DE USUÁRIO ATIVO", text_color="#f39c12")
            btn_cancelar_u.pack(side="left", padx=10)
            u_nome.focus()

        def cancelar_edicao_u():
            u_id.configure(state="normal")
            u_id.delete(0, 'end')
            u_id.configure(state="readonly")
            u_nome.delete(0, 'end')
            u_senha.delete(0, 'end')
            lbl_modo_user.configure(text="NOVO CADASTRO DE USUÁRIO", text_color="#3498db")
            btn_cancelar_u.pack_forget()

        def u_salvar():
            nome = u_nome.get().strip()
            senha = u_senha.get().strip()
            cargo = u_cargo.get()
            
            if not nome or not senha:
                messagebox.showerror("Erro", "Preencha usuário e senha!")
                return
                
            conn = conectar()
            is_update = bool(u_id.get())
            try:
                if is_update:
                    uid = u_id.get()
                    conn.execute("UPDATE usuarios SET username=?, password=?, role=? WHERE id=?", (nome, senha, cargo, uid))
                else:
                    conn.execute("INSERT INTO usuarios (username, password, role) VALUES (?,?,?)", (nome, senha, cargo))
                    
                # A MESMA CORREÇÃO: Commit antes do log
                conn.commit()
                conn.close()
                
                if is_update:
                    registrar_log(usuario_logado, f"Atualizou o usuário #{uid} ({nome}). Cargo: {cargo}")
                    messagebox.showinfo("Sucesso", "Usuário atualizado!")
                else:
                    registrar_log(usuario_logado, f"Cadastrou o novo usuário '{nome}'. Cargo: {cargo}")
                    messagebox.showinfo("Sucesso", "Novo usuário criado!")
            except Exception:
                conn.close()
                messagebox.showerror("Erro", "Nome de usuário já existe no sistema.")
                
            cancelar_edicao_u()
            atualizar_usuarios()

        def u_excluir(uid):
            if str(uid) == "1" or str(uid) == "2":
                messagebox.showerror("Erro", "Não é permitido excluir as contas mestras principais do sistema!")
                return
            if messagebox.askyesno("Cuidado", "Tem certeza que deseja excluir este usuário?"):
                conn = conectar()
                conn.execute("DELETE FROM usuarios WHERE id=?", (uid,))
                conn.commit()
                conn.close()
                registrar_log(usuario_logado, f"Excluiu o usuário de ID #{uid}.")
                atualizar_usuarios()
                messagebox.showinfo("Sucesso", "Usuário Excluído!")

        btn_salvar_u.configure(command=u_salvar)
        btn_cancelar_u.configure(command=cancelar_edicao_u)
        atualizar_usuarios()

    # =========================================================
    # ABA: PERMISSÕES 
    # =========================================================
    if cargo_usuario in ["Admin", "Desenvolvedor"] and (lib_permissoes == 1 or cargo_usuario == "Desenvolvedor"):
        ctk.CTkLabel(tab_permissoes, text="DEFINIR O QUE CADA CARGO PODE ACESSAR", font=("Arial", 16, "bold")).pack(pady=20)
        
        f_p_top = ctk.CTkFrame(tab_permissoes, fg_color="transparent")
        f_p_top.pack(fill="x", padx=40, pady=5)
        ctk.CTkLabel(f_p_top, text="Selecione o Cargo para Configurar:", font=("Arial", 14)).pack(side="left", padx=5)
        cb_cargos_perm = ctk.CTkComboBox(f_p_top, values=["Gerente", "Caixa"], width=200)
        cb_cargos_perm.pack(side="left", padx=15)
        
        f_switches = ctk.CTkFrame(tab_permissoes, fg_color="transparent")
        f_switches.pack(fill="both", expand=True, padx=60, pady=10)
        
        sw_vendas = ctk.CTkSwitch(f_switches, text="Acessar Caixa (PDV)", font=("Arial", 14))
        sw_cadastros = ctk.CTkSwitch(f_switches, text="Acessar Cadastros Gerais", font=("Arial", 14))
        sw_financeiro = ctk.CTkSwitch(f_switches, text="Acessar Menu Financeiro", font=("Arial", 14))
        sw_hist = ctk.CTkSwitch(f_switches, text="Acessar Histórico e Extrato de Clientes", font=("Arial", 14))
        sw_receber = ctk.CTkSwitch(f_switches, text="Visualizar e Receber Contas a Receber (Crediário)", font=("Arial", 14))
        sw_pagar = ctk.CTkSwitch(f_switches, text="Visualizar e Pagar Contas a Pagar", font=("Arial", 14))
        sw_editar_v = ctk.CTkSwitch(f_switches, text="Editar Itens e Estornar Vendas Finalizadas", font=("Arial", 14))
        sw_relatorios = ctk.CTkSwitch(f_switches, text="Gerar Relatórios PDF e Análises de Lucro", font=("Arial", 14))

        dicionario_switches = {"menu_vendas": sw_vendas, "menu_cadastros": sw_cadastros, "menu_financeiro": sw_financeiro,
                               "menu_historico": sw_hist, "aba_receber": sw_receber, "aba_pagar": sw_pagar,
                               "aba_editar_vendas": sw_editar_v, "aba_relatorios": sw_relatorios}

        for sw in dicionario_switches.values():
            sw.pack(anchor="w", pady=5)

        def carregar_permissoes(escolha):
            conn = conectar()
            permissoes = conn.execute("SELECT recurso, permitido FROM permissoes WHERE cargo=?", (escolha,)).fetchall()
            conn.close()
            for sw in dicionario_switches.values(): sw.deselect()
            for rec, status in permissoes:
                if rec in dicionario_switches and status == 1: dicionario_switches[rec].select()

        cb_cargos_perm.configure(command=carregar_permissoes)
        cb_cargos_perm.set("Gerente")
        carregar_permissoes("Gerente")

        def salvar_permissoes():
            cargo_selecionado = cb_cargos_perm.get()
            conn = conectar()
            for recurso, sw in dicionario_switches.items():
                valor = 1 if sw.get() else 0
                conn.execute("UPDATE permissoes SET permitido=? WHERE cargo=? AND recurso=?", (valor, cargo_selecionado, recurso))
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, f"Alterou as permissões estruturais do cargo: {cargo_selecionado}.")
            messagebox.showinfo("Sucesso", "Permissões salvas com sucesso!\nTerão efeito no próximo login dos utilizadores.")

        ctk.CTkFrame(tab_permissoes, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=10)
        
        btn_salvar_perm = ctk.CTkButton(tab_permissoes, text="💾 SALVAR PERMISSÕES", fg_color="green", height=40, font=("Arial", 14, "bold"), command=salvar_permissoes)
        btn_salvar_perm.pack(pady=10)

    # =========================================================
    # ABA: LOGS DE AUDITORIA
    # =========================================================
    if cargo_usuario in ["Admin", "Desenvolvedor"] and (lib_auditoria == 1 or cargo_usuario == "Desenvolvedor"):
        ctk.CTkLabel(tab_logs, text="REGISTRO DE ATIVIDADES DO SISTEMA", font=("Arial", 16, "bold")).pack(pady=10)
        f_l_top = ctk.CTkFrame(tab_logs, fg_color="transparent")
        f_l_top.pack(fill="x", padx=20, pady=5)
        
        ctk.CTkLabel(f_l_top, text="Data Inicial:").pack(side="left", padx=5)
        ent_log_ini = ctk.CTkEntry(f_l_top, width=110, placeholder_text="DD/MM/AAAA")
        ent_log_ini.pack(side="left", padx=5)
        ent_log_ini.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        ctk.CTkLabel(f_l_top, text="Data Final:").pack(side="left", padx=5)
        ent_log_fim = ctk.CTkEntry(f_l_top, width=110, placeholder_text="DD/MM/AAAA")
        ent_log_fim.pack(side="left", padx=5)
        ent_log_fim.insert(0, datetime.now().strftime("%d/%m/%Y"))
        
        txt_logs = ctk.CTkTextbox(tab_logs, font=("Courier New", 13))
        txt_logs.pack(fill="both", expand=True, padx=20, pady=10)

        def buscar_logs():
            try:
                d_ini = datetime.strptime(ent_log_ini.get(), "%d/%m/%Y").strftime("%Y-%m-%d 00:00:00")
                d_fim = datetime.strptime(ent_log_fim.get(), "%d/%m/%Y").strftime("%Y-%m-%d 23:59:59")
            except:
                messagebox.showerror("Erro", "Datas inválidas. Utilize o formato correto: DD/MM/AAAA")
                return
            txt_logs.delete("1.0", "end")
            conn = conectar()
            logs = conn.execute("SELECT data_hora, usuario, acao FROM logs WHERE data_hora BETWEEN ? AND ? ORDER BY data_hora DESC", (d_ini, d_fim)).fetchall()
            conn.close()
            txt_logs.insert("end", f"{'DATA/HORA':<20} | {'USUÁRIO':<15} | {'AÇÃO REALIZADA'}\n{'-'*80}\n")
            if not logs: txt_logs.insert("end", "Nenhum registro encontrado neste período.")
            for l in logs: txt_logs.insert("end", f"{l[0]:<20} | {l[1]:<15} | {l[2]}\n")

        ctk.CTkButton(f_l_top, text="BUSCAR LOGS", fg_color="#3498db", command=buscar_logs).pack(side="left", padx=15)
        buscar_logs()

    # =========================================================
    # ABA: LICENÇA E STATUS
    # =========================================================
    if cargo_usuario == "Desenvolvedor":
        def render_licenca():
            for w in tab_dev.winfo_children(): w.destroy()
            ctk.CTkLabel(tab_dev, text="CONTROLE DE ACESSO E LICENCIAMENTO", font=("Arial", 22, "bold")).pack(pady=20)
            f_info = ctk.CTkFrame(tab_dev, border_width=2, border_color="#3498db", fg_color="transparent")
            f_info.pack(padx=50, pady=20, fill="x")
            
            ativa, motivo = verificar_licenca_db()
            conn = conectar()
            lic = conn.execute("SELECT chave, data_expiracao FROM licenca WHERE id=1").fetchone()
            conn.close()
            
            status_txt = "🔴 SISTEMA NÃO ATIVADO"
            cor_status = "#e74c3c"
            detalhe_txt = motivo

            if ativa:
                cor_status = "#2ecc71"
                if lic and "VITALICIO" in str(lic[0]).upper():
                    status_txt = "🟢 STATUS: ATIVADO"
                    detalhe_txt = "TIPO DE LICENÇA: ✨ VITALÍCIA (PERMANENTE)"
                elif lic and lic[1]:
                    try:
                        exp = datetime.strptime(lic[1], "%Y-%m-%d")
                        dias_restantes = (exp - datetime.now()).days
                        if dias_restantes < 0:
                            status_txt = "🔴 STATUS: EXPIRADO"
                            cor_status = "#e74c3c"
                            detalhe_txt = "A SUA LICENÇA DE AVALIAÇÃO EXPIROU."
                        else:
                            status_txt = "🟢 STATUS: ATIVADO"
                            detalhe_txt = f"MODO AVALIAÇÃO: FALTAM {dias_restantes} DIAS PARA EXPIRAR"
                    except:
                        detalhe_txt = "ERRO AO CALCULAR DATA DE EXPIRAÇÃO"

            ctk.CTkLabel(f_info, text=status_txt, font=("Arial", 24, "bold"), text_color=cor_status).pack(pady=15)
            ctk.CTkLabel(f_info, text=detalhe_txt, font=("Arial", 16, "bold")).pack(pady=(0, 15))

            ctk.CTkLabel(tab_dev, text="INSERIR NOVA CHAVE DE ATIVAÇÃO:", font=("Arial", 14, "bold")).pack(pady=(20, 5))
            e_chave = ctk.CTkEntry(tab_dev, width=400, show="*", placeholder_text="Cole sua chave de ativação aqui...")
            e_chave.pack(pady=10)
            
            def realizar_ativacao():
                res, msg = ativar_licenca(e_chave.get().strip())
                if res:
                    messagebox.showinfo("Sucesso", "Sistema ativado com sucesso!")
                    render_licenca()
                else:
                    messagebox.showerror("Erro", "Chave de ativação inválida ou expirada!")

            ctk.CTkButton(tab_dev, text="ATIVAR AGORA", fg_color="green", height=40, font=("Arial", 14, "bold"), command=realizar_ativacao).pack(pady=15)
            ctk.CTkLabel(tab_dev, text="Aviso de Segurança: Apenas partilhe chaves com clientes autorizados.", text_color="gray").pack(pady=10)

        render_licenca()

    # =========================================================
    # ABA: CUSTOMIZAÇÃO (WHITE LABEL)
    # =========================================================
    if cargo_usuario == "Desenvolvedor":
        conn = conectar()
        res = conn.execute("SELECT nome_sistema, ver_vendedores, ver_contas_pagar, ver_dados_empresa, ver_usuarios, ver_permissoes, ver_auditoria, auto_backup, ver_orcamentos, ver_num_pedido, ver_cod_barras FROM configuracoes WHERE id=1").fetchone()
        conn.close()

        ctk.CTkLabel(tab_custom, text="CONTROLE WHITE LABEL (LIBERAR/BLOQUEAR RECURSOS)", font=("Arial", 16, "bold"), text_color="#e67e22").pack(pady=10)
        
        f_custom = ctk.CTkScrollableFrame(tab_custom, fg_color="transparent")
        f_custom.pack(fill="both", expand=True, padx=20, pady=5)
        
        ctk.CTkLabel(f_custom, text="Nome do Sistema (Exibido no Topo e Relatórios):", font=("Arial", 12, "bold")).pack(anchor="w", padx=20)
        ent_nome_sistema = ctk.CTkEntry(f_custom, width=350)
        ent_nome_sistema.pack(anchor="w", padx=20, pady=(5, 20))
        ent_nome_sistema.insert(0, res[0])

        sw_auto_bkp = ctk.CTkSwitch(f_custom, text="Ativar Backup Automático ao Logout")
        sw_auto_bkp.pack(anchor="w", padx=20, pady=10)
        if res[7] == 1: sw_auto_bkp.select()

        sw_cod_barras = ctk.CTkSwitch(f_custom, text="Habilitar campo 'Código de Barras' no Cadastro de Produtos", progress_color="#8e44ad")
        sw_cod_barras.pack(anchor="w", padx=20, pady=10)
        if res[10] == 1: sw_cod_barras.select()

        sw_orcamentos = ctk.CTkSwitch(f_custom, text="Liberar Função de Orçamentos/Pré-Venda no Caixa", progress_color="#f39c12")
        sw_orcamentos.pack(anchor="w", padx=20, pady=10)
        if res[8] == 1: sw_orcamentos.select()

        sw_num_pedido = ctk.CTkSwitch(f_custom, text="Exibir 'Próximo Pedido' no topo do Caixa", progress_color="#3498db")
        sw_num_pedido.pack(anchor="w", padx=20, pady=10)
        if res[9] == 1: sw_num_pedido.select()

        sw_vendedores = ctk.CTkSwitch(f_custom, text="Liberar Aba Vendedores (Cadastros) e Menu no PDV")
        sw_vendedores.pack(anchor="w", padx=20, pady=10)
        if res[1] == 1: sw_vendedores.select()

        sw_c_pagar = ctk.CTkSwitch(f_custom, text="Liberar Aba 'Contas a Pagar' dentro do Financeiro")
        sw_c_pagar.pack(anchor="w", padx=20, pady=10)
        if res[2] == 1: sw_c_pagar.select()

        sw_empresa = ctk.CTkSwitch(f_custom, text="Liberar Aba 'Dados da Empresa' nas Configurações")
        sw_empresa.pack(anchor="w", padx=20, pady=10)
        if res[3] == 1: sw_empresa.select()

        sw_usuarios = ctk.CTkSwitch(f_custom, text="Liberar Aba 'Usuários' nas Configurações")
        sw_usuarios.pack(anchor="w", padx=20, pady=10)
        if res[4] == 1: sw_usuarios.select()

        sw_perm = ctk.CTkSwitch(f_custom, text="Liberar Aba 'Permissões' nas Configurações")
        sw_perm.pack(anchor="w", padx=20, pady=10)
        if res[5] == 1: sw_perm.select()

        sw_auditoria = ctk.CTkSwitch(f_custom, text="Liberar Aba 'Logs de Auditoria' nas Configurações")
        sw_auditoria.pack(anchor="w", padx=20, pady=10)
        if res[6] == 1: sw_auditoria.select()

        def salvar_customizacao():
            n = ent_nome_sistema.get()
            v = 1 if sw_vendedores.get() else 0
            p = 1 if sw_c_pagar.get() else 0
            e = 1 if sw_empresa.get() else 0
            u = 1 if sw_usuarios.get() else 0
            perm = 1 if sw_perm.get() else 0
            a = 1 if sw_auditoria.get() else 0
            ab = 1 if sw_auto_bkp.get() else 0
            orc = 1 if sw_orcamentos.get() else 0
            num_p = 1 if sw_num_pedido.get() else 0
            c_barras = 1 if sw_cod_barras.get() else 0
            
            conn = conectar()
            conn.execute("UPDATE configuracoes SET nome_sistema=?, ver_vendedores=?, ver_contas_pagar=?, ver_dados_empresa=?, ver_usuarios=?, ver_permissoes=?, ver_auditoria=?, auto_backup=?, ver_orcamentos=?, ver_num_pedido=?, ver_cod_barras=? WHERE id=1", (n, v, p, e, u, perm, a, ab, orc, num_p, c_barras))
            conn.commit()
            conn.close()
            registrar_log(usuario_logado, "Atualizou as configurações do White Label (Controle de Recursos).")
            messagebox.showinfo("Sucesso", "Configurações White Label aplicadas!\nReinicie o sistema para ver as mudanças refletidas nos menus.")

        ctk.CTkFrame(tab_custom, height=2, fg_color="#2c3e50").pack(fill="x", padx=20, pady=10)
        ctk.CTkButton(tab_custom, text="APLICAR MUDANÇAS", fg_color="green", height=40, font=("Arial", 14, "bold"), command=salvar_customizacao).pack(pady=10)

    f_sup = ctk.CTkFrame(container, fg_color="transparent")
    f_sup.pack(fill="x", side="bottom", pady=10)
    ctk.CTkLabel(f_sup, text=f"Sistema Master Pro  |  Dev: {NOME_DESENVOLVEDOR}  |  WhatsApp: {TELEFONE_SUPORTE}", font=("Arial", 12, "bold"), text_color="#7f8c8d").pack()
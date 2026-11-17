import customtkinter as ctk
from tkinter import messagebox
import os
import shutil
from datetime import datetime

# Importações da base do sistema
from seguranca import verificar_licenca_db, TelaAtivacao, TelaLogin
from database import (aplicar_configuracoes_globais, conectar, 
                      verificar_permissao, registrar_log, DB_PATH, DIRETORIO_BASE)

# Importação dos módulos das telas
from telas.cadastros import setup_cadastros
from telas.financeiro import setup_financeiro
from telas.pdv_caixa import setup_vendas
from telas.configs import setup_configuracoes

class SistemaERP_Modular(ctk.CTk):
    def __init__(self, usuario_logado, cargo_usuario):
        super().__init__()
        
        self.usuario_logado = usuario_logado
        self.cargo_usuario = cargo_usuario
        
        registrar_log(self.usuario_logado, "Fez login no sistema.")
        
        conn = conectar()
        self.conf_sis = conn.execute("SELECT nome_sistema, descanso_tela, tempo_descanso FROM configuracoes WHERE id=1").fetchone()
        conn.close()
        
        self.nome_sis = self.conf_sis[0] if self.conf_sis else "MASTER PRO"

        self.title(f"{self.nome_sis} - Sessão: {self.usuario_logado} ({self.cargo_usuario})")
        self.geometry("1250x850")
        
        try:
            self.after(250, lambda: self.state('zoomed'))
        except:
            pass

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # =======================================================
        # BARRA LATERAL (MENU)
        # =======================================================
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text=self.nome_sis, font=("Arial", 22, "bold"), text_color="#3498db").pack(pady=30)
        
        menu_itens = [
            ("🛒 CAIXA (PDV)", "vendas", None), 
            ("📋 CADASTROS", "cadastros", "#8e44ad"), 
            ("💰 FINANCEIRO", "financeiro", "#d35400")
        ]
        
        for txt, aba, cor in menu_itens:
            if not verificar_permissao(self.cargo_usuario, f"menu_{aba}"):
                continue
                
            ctk.CTkButton(self.sidebar, text=txt, fg_color=cor, font=("Arial", 13, "bold"), height=40, command=lambda a=aba: self.mostrar_aba(a)).pack(pady=10, padx=20)

        ctk.CTkButton(self.sidebar, text="Sair (Logout)", fg_color="#c0392b", hover_color="#e74c3c", command=self.fazer_logout).pack(side="bottom", pady=20, padx=20)
        
        if self.cargo_usuario in ["Desenvolvedor", "Admin", "Gerente"]:
            ctk.CTkButton(self.sidebar, text="⚙️ CONFIGURAÇÕES", fg_color="#2c3e50", command=lambda: self.mostrar_aba("config")).pack(side="bottom", pady=0, padx=20)

        # =======================================================
        # CONTAINER PRINCIPAL
        # =======================================================
        self.container = ctk.CTkFrame(self, corner_radius=15, fg_color="transparent")
        self.container.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.abas = {}
        self.abas["vendas"] = ctk.CTkFrame(self.container)
        setup_vendas(self.abas["vendas"], self.usuario_logado, self.cargo_usuario)
        
        self.abas["cadastros"] = ctk.CTkFrame(self.container)
        # ESTA LINHA FOI CORRIGIDA PARA ENVIAR O usuario_logado:
        setup_cadastros(self.abas["cadastros"], self.usuario_logado, self.cargo_usuario)
        
        self.abas["financeiro"] = ctk.CTkFrame(self.container)
        setup_financeiro(self.abas["financeiro"], self.usuario_logado, self.cargo_usuario)
        
        self.abas["config"] = ctk.CTkFrame(self.container)
        setup_configuracoes(self.abas["config"], self.usuario_logado, self.cargo_usuario)
        
        if verificar_permissao(self.cargo_usuario, "menu_vendas"): 
            self.mostrar_aba("vendas")
        elif verificar_permissao(self.cargo_usuario, "menu_financeiro"): 
            self.mostrar_aba("financeiro")
        else: 
            self.mostrar_aba("config")

        # =======================================================
        # SISTEMA DE DESCANSO DE TELA
        # =======================================================
        self.descanso_ativo = False
        
        self.usar_descanso = self.conf_sis[1] == 1 if self.conf_sis else False
        self.tempo_descanso_ms = (self.conf_sis[2] if self.conf_sis else 5) * 60000
        self.ultimo_evento = datetime.now()
        
        if self.usar_descanso:
            self.bind_all("<Any-KeyPress>", self.registrar_atividade)
            self.bind_all("<Any-ButtonPress>", self.registrar_atividade)
            self.bind_all("<Motion>", self.registrar_atividade)
            self.verificar_inatividade()

    def mostrar_aba(self, nome):
        for aba in self.abas.values(): 
            aba.pack_forget()
        self.abas[nome].pack(fill="both", expand=True)

    def registrar_atividade(self, event=None):
        self.ultimo_evento = datetime.now()
        if self.descanso_ativo:
            self.sair_descanso()

    def verificar_inatividade(self):
        if not self.descanso_ativo:
            tempo_ocioso = (datetime.now() - self.ultimo_evento).total_seconds() * 1000
            if tempo_ocioso >= self.tempo_descanso_ms:
                self.ativar_descanso()
        self.after(2000, self.verificar_inatividade)

    def ativar_descanso(self):
        if self.descanso_ativo: return
        self.descanso_ativo = True
        
        self.tela_preta = ctk.CTkToplevel(self)
        largura_tela = self.winfo_screenwidth()
        altura_tela = self.winfo_screenheight()
        
        self.tela_preta.geometry(f"{largura_tela}x{altura_tela}+0+0")
        self.tela_preta.overrideredirect(True)
        self.tela_preta.attributes('-topmost', True)
        self.tela_preta.configure(fg_color="#0a0a0a")
        
        self.lbl_relogio = ctk.CTkLabel(self.tela_preta, text="", font=("Courier New", 90, "bold"), text_color="#3498db")
        self.lbl_relogio.place(relx=0.5, rely=0.45, anchor="center")
        
        self.lbl_nome = ctk.CTkLabel(self.tela_preta, text=self.nome_sis, font=("Arial", 30), text_color="#7f8c8d")
        self.lbl_nome.place(relx=0.5, rely=0.6, anchor="center")
        
        self.atualizar_relogio_descanso()
        
        self.tela_preta.bind("<Any-KeyPress>", self.sair_descanso)
        self.tela_preta.bind("<Any-ButtonPress>", self.sair_descanso)
        self.tela_preta.bind("<Motion>", self.sair_descanso)

    def atualizar_relogio_descanso(self):
        if self.descanso_ativo and hasattr(self, 'lbl_relogio') and self.lbl_relogio.winfo_exists():
            agora = datetime.now().strftime("%H:%M:%S")
            self.lbl_relogio.configure(text=agora)
            self.tela_preta.after(1000, self.atualizar_relogio_descanso)

    def sair_descanso(self, event=None):
        if self.descanso_ativo:
            self.descanso_ativo = False
            if hasattr(self, 'tela_preta'):
                self.tela_preta.destroy()
            self.ultimo_evento = datetime.now()

    def fazer_logout(self):
        try:
            conn = conectar()
            r = conn.execute("SELECT auto_backup FROM configuracoes WHERE id=1").fetchone()
            conn.close()
            
            if r and r[0] == 1:
                p_auto = os.path.join(DIRETORIO_BASE, "backups_automaticos")
                if not os.path.exists(p_auto): os.makedirs(p_auto)
                nome_bkp = f"auto_{self.usuario_logado}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(DB_PATH, os.path.join(p_auto, nome_bkp))
                
                dt_bkp = datetime.now().strftime("%d/%m/%Y %H:%M")
                conn = conectar()
                conn.execute("UPDATE configuracoes SET ultimo_backup=? WHERE id=1", (dt_bkp,))
                conn.commit()
                conn.close()
        except: pass

        registrar_log(self.usuario_logado, "Fez logout do sistema.")
        self.destroy()

def rodar_sistema():
    aplicar_configuracoes_globais()
    if not verificar_licenca_db()[0]:
        app_ativ = TelaAtivacao("Licença Requerida")
        app_ativ.mainloop()
        if not app_ativ.ok: return
            
    while True:
        login = TelaLogin()
        login.mainloop()
        if login.ok:
            app = SistemaERP_Modular(login.username, login.user_role)
            app.mainloop()
        else:
            break

if __name__ == "__main__":
    rodar_sistema()
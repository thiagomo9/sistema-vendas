import customtkinter as ctk
from tkinter import messagebox
import subprocess
from datetime import datetime, timedelta

# Importa a conexão do nosso banco de dados
from database import conectar

# =================================================================
# DADOS DO DESENVOLVEDOR E CHAVES DE ACESSO
# =================================================================
CHAVES_CADASTRADAS = {
    "TESTE30": 30,            
    "PRO-VITALICIO": 36500    
}

NOME_DESENVOLVEDOR = "Thiago"
TELEFONE_SUPORTE = "(79) 98149-1530"

# =================================================================
# LÓGICA DE LICENCIAMENTO
# =================================================================
def obter_id_maquina():
    """Captura o ID físico da placa-mãe para travar o sistema neste PC."""
    try:
        return subprocess.check_output('wmic csproduct get uuid', shell=True).decode().split('\n')[1].strip()
    except:
        return "ERRO-HARDWARE"

def verificar_licenca_db():
    hwid_atual = obter_id_maquina()
    conn = conectar()
    lic = conn.execute("SELECT hwid, data_expiracao FROM licenca WHERE id=1").fetchone()
    conn.close()

    if lic:
        hwid_salvo, data_exp_str = lic
        
        # O PC não é o mesmo que ativou o sistema
        if hwid_salvo != hwid_atual:
            return False, "hardware_diferente"
            
        # A data expirou
        data_expiracao = datetime.strptime(data_exp_str, "%Y-%m-%d")
        if datetime.now() > data_expiracao:
            return False, "expirada"
            
        return True, "ok" 
        
    return False, "sem_licenca"

def ativar_licenca(chave_digitada):
    if chave_digitada in CHAVES_CADASTRADAS:
        dias_validade = CHAVES_CADASTRADAS[chave_digitada]
        data_exp = (datetime.now() + timedelta(days=dias_validade)).strftime("%Y-%m-%d")
        hwid_atual = obter_id_maquina()
        
        conn = conectar()
        conn.execute("DELETE FROM licenca")
        conn.execute("INSERT INTO licenca (id, hwid, chave, data_expiracao) VALUES (1, ?, ?, ?)", (hwid_atual, chave_digitada, data_exp))
        conn.commit()
        conn.close()
        
        return True, data_exp
        
    return False, None

# =================================================================
# TELAS DE SEGURANÇA (BLOQUEIO E LOGIN)
# =================================================================
class TelaAtivacao(ctk.CTk):
    """Tela exibida apenas se o sistema estiver bloqueado."""
    def __init__(self, motivo_bloqueio):
        super().__init__()
        self.geometry("450x380")
        self.eval('tk::PlaceWindow . center')
        self.title("Ativação do Sistema")
        self.ok = False
        
        f = ctk.CTkFrame(self)
        f.pack(pady=30, padx=30, fill="both", expand=True)
        
        ctk.CTkLabel(f, text="🔒 SISTEMA BLOQUEADO", font=("Arial", 20, "bold"), text_color="#e74c3c").pack(pady=20)
        
        msg = f"Insira sua chave de ativação para continuar.\nPara adquirir a licença, contate:\n{NOME_DESENVOLVEDOR} - Tel: {TELEFONE_SUPORTE}"
        
        if motivo_bloqueio == "expirada":
            msg = f"Sua licença expirou!\nAdquira a versão vitalícia com:\n{NOME_DESENVOLVEDOR} - Tel: {TELEFONE_SUPORTE}"
        elif motivo_bloqueio == "hardware_diferente":
            msg = f"Licença inválida para este computador.\nContate o suporte:\n{NOME_DESENVOLVEDOR} - Tel: {TELEFONE_SUPORTE}"
            
        ctk.CTkLabel(f, text=msg, font=("Arial", 12), text_color="gray").pack(pady=10)
        
        self.c = ctk.CTkEntry(f, show="*", width=300, placeholder_text="Digite a Chave...")
        self.c.pack(pady=10)
        
        ctk.CTkButton(f, text="ATIVAR SISTEMA", font=("Arial", 14, "bold"), height=40, fg_color="#27ae60", hover_color="#2ecc71", command=self.ativar).pack(pady=20)
        
    def ativar(self):
        sucesso, validade = ativar_licenca(self.c.get().strip())
        if sucesso:
            messagebox.showinfo("Sucesso", f"Sistema ativado!\nSua licença é válida até: {validade}")
            self.ok = True
            self.destroy()
        else:
            messagebox.showerror("Erro", "Chave Inválida ou Incorreta.")

class TelaLogin(ctk.CTk):
    """Tela de acesso ao ERP."""
    def __init__(self):
        super().__init__()
        self.geometry("400x500")
        self.eval('tk::PlaceWindow . center')
        self.title("Acesso ao Sistema")
        
        self.ok = False
        self.username = None
        self.user_role = None
        
        f = ctk.CTkFrame(self)
        f.pack(pady=40, padx=40, fill="both", expand=True)
        
        ctk.CTkLabel(f, text="ERP MASTER PRO", font=("Arial", 24, "bold"), text_color="#3498db").pack(pady=40)
        
        self.u = ctk.CTkEntry(f, placeholder_text="Usuário", width=250, height=40)
        self.u.pack(pady=10)
        
        self.s = ctk.CTkEntry(f, placeholder_text="Senha", show="*", width=250, height=40)
        self.s.pack(pady=10)
        self.s.bind("<Return>", lambda e: self.logar())
        
        ctk.CTkButton(f, text="ENTRAR", font=("Arial", 14, "bold"), width=250, height=45, command=self.logar).pack(pady=30)
        
    def logar(self):
        conn = conectar()
        r = conn.execute("SELECT role FROM usuarios WHERE username=? AND password=?", (self.u.get(), self.s.get())).fetchone()
        conn.close()
        
        if r:
            self.ok = True
            self.username = self.u.get()
            self.user_role = r[0]
            self.destroy()
        else:
            messagebox.showerror("Acesso Negado", "Usuário ou senha incorretos!")
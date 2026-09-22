from typing import Optional
from datetime import datetime
from database import Base, engine, get_db
from fastapi import Depends, FastAPI, Form, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import models
import services
from sqlalchemy.orm import Session
from datetime import date

app = FastAPI(title="LensAgenda", version="3.5")
templates = Jinja2Templates(directory="templates")

# Cria as tabelas automaticamente se não existirem
Base.metadata.create_all(bind=engine)


@app.on_event("startup")
def startup_event():
    db = next(get_db())
    services.LensAgendaService.inicializar_admin_padrao(db)
    db.close()


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, erro: str = None):
    return templates.TemplateResponse(
        request, "login.html", {"erro": erro}
    )


@app.post("/login")
def login_action(
    response: Response,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = services.LensAgendaService.autenticar_utilizador(
        db, username, password
    )
    if user:
        redirecionar = RedirectResponse(url="/", status_code=303)
        redirecionar.set_cookie(
            key="session_user", value=user.nome, httponly=True)
        return redirecionar
    else:
        return RedirectResponse(
            url="/login?erro=Utilizador+ou+password+incorretos", status_code=303
        )


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request, erro: str = None):
    return templates.TemplateResponse(
        request, "register.html", {"erro": erro}
    )


@app.post("/register")
def register_action(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    sucesso, mensagem = services.LensAgendaService.criar_utilizador(
        db, username, password
    )
    if sucesso:
        return RedirectResponse(
            url="/login?erro=Conta+criada+com+sucesso!+Pode+entrar.", status_code=303
        )
    else:
        from urllib.parse import quote

        return RedirectResponse(
            url=f"/register?erro={quote(mensagem)}", status_code=303
        )


@app.get("/logout")
def logout(response: Response):
    redirecionar = RedirectResponse(url="/login", status_code=303)
    redirecionar.delete_cookie(key="session_user")
    return redirecionar


@app.get("/", response_class=HTMLResponse)
def read_root(
    request: Request,
    mes: Optional[str] = None,
    ano: Optional[str] = None,
    db: Session = Depends(get_db),
):
  utilizador_atual = request.cookies.get("session_user")
  if not utilizador_atual:
    return RedirectResponse(url="/login", status_code=303)

  hoje = date.today()

  # Conversão segura para inteiro (funciona se vier string, vazio ou int)
  mes_int = None
  if mes is not None and str(mes).strip() != "":
    try:
      mes_int = int(mes)
    except ValueError:
      pass

  ano_int = None
  if ano is not None and str(ano).strip() != "":
    try:
      ano_int = int(ano)
    except ValueError:
      pass

  # Se nenhum filtro foi passado, assume o mês e ano correntes
  if mes is None and ano is None:
    mes_int = hoje.month
    ano_int = hoje.year

  eventos_agenda = services.LensAgendaService.listar_eventos_por_utilizador(
      db, utilizador_atual
  )
  eventos_financeiros = (
      services.LensAgendaService.listar_eventos_filtrados(
          db, utilizador_atual, mes=mes_int, ano=ano_int
      )
  )

  organizadores = services.LensAgendaService.listar_organizadores(
      db, utilizador_atual
  )
  anos_disponiveis = services.LensAgendaService.obter_anos_disponiveis(
      db, utilizador_atual
  )
  comparativo_historico = (
      services.LensAgendaService.obter_comparativo_historico(
          db, utilizador_atual
      )
  )

  return templates.TemplateResponse(
      request,
      "index.html",
      {
          "eventos": eventos_agenda,
          "eventos_financeiros": eventos_financeiros,
          "organizadores": organizadores,
          "utilizador_atual": utilizador_atual,
          "mes_atual": mes_int if mes_int else "",
          "ano_atual": ano_int if ano_int else "",
          "anos_disponiveis": anos_disponiveis,
          "comparativo_historico": comparativo_historico,
      },
  )

@app.post("/organizadores/novo")
def criar_organizador(
    request: Request, nome: str = Form(...), db: Session = Depends(get_db)
):
    if not request.cookies.get("session_user"):
        return RedirectResponse(url="/login", status_code=303)
    services.LensAgendaService.adicionar_organizador(db, nome)
    return RedirectResponse(url="/", status_code=303)


@app.post("/eventos/novo")
def criar_evento(
    request: Request,
    nome_evento: str = Form(...),
    organizador_id: int = Form(...),
    data: str = Form(...),
    horario: str = Form(None),
    local: str = Form(None),
    custos: float = Form(0.0),
    vendas: float = Form(0.0),
    db: Session = Depends(get_db),
):
    utilizador_atual = request.cookies.get("session_user")
    if not utilizador_atual:
        return RedirectResponse(url="/login", status_code=303)

    data_obj = datetime.strptime(data, "%Y-%m-%d").date()

    dados = {
        "utilizador": utilizador_atual,
        "nome_evento": nome_evento,
        "organizador_id": organizador_id,
        "data": data_obj,
        "ano": data_obj.year,
        "horario": horario,
        "local": local,
        "custos": custos,
        "vendas": vendas,
    }

    services.LensAgendaService.criar_evento(db, dados)
    return RedirectResponse(url="/", status_code=303)


@app.get("/eventos/{evento_id}/editar", response_class=HTMLResponse)
def editar_evento_page(
    request: Request, evento_id: int, db: Session = Depends(get_db)
):
    utilizador_atual = request.cookies.get("session_user")
    if not utilizador_atual:
        return RedirectResponse(url="/login", status_code=303)

    evento = services.LensAgendaService.obter_evento_por_id(db, evento_id)
    if not evento or evento.utilizador != utilizador_atual:
        return RedirectResponse(url="/", status_code=303)

    organizadores = services.LensAgendaService.listar_organizadores(db)

    return templates.TemplateResponse(
        request,
        "editar_evento.html",
        {
            "evento": evento,
            "organizadores": organizadores,
            "utilizador_atual": utilizador_atual,
        },
    )


@app.post("/eventos/{evento_id}/editar")
def editar_evento_action(
    request: Request,
    evento_id: int,
    nome_evento: str = Form(...),
    organizador_id: int = Form(...),
    data: str = Form(...),
    horario: str = Form(None),
    local: str = Form(None),
    custos: float = Form(0.0),
    vendas: float = Form(0.0),
    db: Session = Depends(get_db),
):
    utilizador_atual = request.cookies.get("session_user")
    if not utilizador_atual:
        return RedirectResponse(url="/login", status_code=303)

    evento = services.LensAgendaService.obter_evento_por_id(db, evento_id)
    if not evento or evento.utilizador != utilizador_atual:
        return RedirectResponse(url="/", status_code=303)

    data_obj = datetime.strptime(data, "%Y-%m-%d").date()

    dados = {
        "nome_evento": nome_evento,
        "organizador_id": organizador_id,
        "data": data_obj,
        "ano": data_obj.year,
        "horario": horario,
        "local": local,
        "custos": custos,
        "vendas": vendas,
    }

    services.LensAgendaService.atualizar_evento(db, evento_id, dados)
    return RedirectResponse(url="/", status_code=303)


@app.post("/eventos/{evento_id}/apagar")
def apagar_evento(request: Request, evento_id: int, db: Session = Depends(get_db)):
    utilizador_atual = request.cookies.get("session_user")
    if not utilizador_atual:
        return RedirectResponse(url="/login", status_code=303)

    evento = services.LensAgendaService.obter_evento_por_id(db, evento_id)
    if evento and evento.utilizador == utilizador_atual:
        services.LensAgendaService.eliminar_evento(db, evento_id)

    return RedirectResponse(url="/", status_code=303)

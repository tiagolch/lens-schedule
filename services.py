import hashlib
from datetime import date
from models import EventoModel, OrganizadorModel, UtilizadorModel
from sqlalchemy import extract
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class LensAgendaService:

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def criar_utilizador(db: Session, nome: str, password: str) -> tuple[bool, str]:
        nome_limpo = nome.strip()
        if not nome_limpo or not password:
            return False, "Nome e password são obrigatórios."
        try:
            hash_pw = LensAgendaService._hash_password(password)
            novo = UtilizadorModel(nome=nome_limpo, password_hash=hash_pw)
            db.add(novo)
            db.commit()
            return True, f"Utilizador '{nome_limpo}' criado com sucesso!"
        except IntegrityError:
            db.rollback()
            return False, "Este utilizador já existe."

    @staticmethod
    def autenticar_utilizador(db: Session, nome: str, password: str):
        user = (
            db.query(UtilizadorModel).filter(
                UtilizadorModel.nome == nome).first()
        )
        if user and user.password_hash == LensAgendaService._hash_password(
            password
        ):
            return user
        return None

    @staticmethod
    def inicializar_admin_padrao(db: Session):
        if db.query(UtilizadorModel).count() == 0:
            LensAgendaService.criar_utilizador(db, "tiago", "admin123")

    @staticmethod
    def listar_organizadores(db: Session, utilizador_id: int, incluir_organizador_id: int = None):
        query = db.query(OrganizadorModel).filter(
            OrganizadorModel.utilizador_id == utilizador_id
        )
        organizadores = query.order_by(OrganizadorModel.nome.asc()).all()
        
        if incluir_organizador_id:
            ids_existentes = [o.id for o in organizadores]
            if incluir_organizador_id not in ids_existentes:
                org_extra = db.query(OrganizadorModel).filter(OrganizadorModel.id == incluir_organizador_id).first()
                if org_extra:
                    organizadores.append(org_extra)
                    organizadores.sort(key=lambda x: x.nome.lower())

        return organizadores

    @staticmethod
    def adicionar_organizador(
        db: Session, utilizador_id: int, nome: str
    ) -> tuple[bool, str]:
        nome_limpo = nome.strip()
        if not nome_limpo:
            return False, "O nome do organizador não pode estar vazio."
        try:
            novo = OrganizadorModel(utilizador_id=utilizador_id, nome=nome_limpo)
            db.add(novo)
            db.commit()
            return True, f"Organizador '{nome_limpo}' adicionado com sucesso!"
        except IntegrityError:
            db.rollback()
            return False, "Este organizador já se encontra registado na sua conta."

    @staticmethod
    def criar_evento(db: Session, dados: dict) -> tuple[bool, str]:
        try:
            if "data" in dados and "ano" not in dados:
                dados["ano"] = dados["data"].year
            novo_evento = EventoModel(**dados)
            db.add(novo_evento)
            db.commit()
            return True, "Evento registado com sucesso!"
        except Exception as e:
            db.rollback()
            return False, f"Erro ao registar evento: {str(e)}"

    @staticmethod
    def listar_eventos_por_utilizador(db: Session, utilizador_id: int):
        return (
            db.query(EventoModel)
            .filter(EventoModel.utilizador_id == utilizador_id)
            .order_by(EventoModel.data.desc())
            .all()
        )

    @staticmethod
    def obter_evento_por_id(db: Session, evento_id: int):
        return db.query(EventoModel).filter(EventoModel.id == evento_id).first()

    @staticmethod
    def atualizar_evento(
        db: Session, evento_id: int, dados: dict
    ) -> tuple[bool, str]:
        try:
            evento = (
                db.query(EventoModel).filter(
                    EventoModel.id == evento_id).first()
            )
            if evento:
                if "data" in dados and dados["data"]:
                    dados["ano"] = dados["data"].year
                for chave, valor in dados.items():
                    setattr(evento, chave, valor)
                db.commit()
                return True, "Evento atualizado com sucesso!"
            return False, "Evento não encontrado."
        except Exception as e:
            db.rollback()
            return False, f"Erro ao atualizar: {str(e)}"

    @staticmethod
    def eliminar_evento(db: Session, evento_id: int) -> tuple[bool, str]:
        try:
            evento = (
                db.query(EventoModel).filter(
                    EventoModel.id == evento_id).first()
            )
            if evento:
                db.delete(evento)
                db.commit()
                return True, "Evento eliminado com sucesso!"
            return False, "Evento não encontrado."
        except Exception as e:
            db.rollback()
            return False, f"Erro ao eliminar evento: {str(e)}"

    @staticmethod
    def listar_eventos_filtrados(
        db: Session, utilizador_id: int, mes: int = None, ano: int = None
    ):
        query = db.query(EventoModel).filter(
            EventoModel.utilizador_id == utilizador_id)

        if ano:
            query = query.filter(EventoModel.ano == ano)

        if mes:
            query = query.filter(extract("month", EventoModel.data) == mes)

        return query.order_by(EventoModel.data.desc()).all()

    @staticmethod
    def obter_anos_disponiveis(db: Session, utilizador_id: int):
        anos = (
            db.query(EventoModel.ano)
            .filter(EventoModel.utilizador_id == utilizador_id)
            .distinct()
            .order_by(EventoModel.ano.desc())
            .all()
        )
        return [a[0] for a in anos]

    @staticmethod
    def obter_comparativo_historico(db: Session, utilizador_id: int):
        eventos = (
            db.query(EventoModel)
            .filter(EventoModel.utilizador_id == utilizador_id)
            .all()
        )
        comparativo = {}
        for ev in eventos:
            chave = ev.nome_evento.strip()
            if chave not in comparativo:
                comparativo[chave] = []

            lucro = (ev.vendas or 0.0) - (ev.custos or 0.0)
            comparativo[chave].append({
                "id": ev.id,
                "ano": ev.ano,
                "data": ev.data,
                "vendas": ev.vendas or 0.0,
                "custos": ev.custos or 0.0,
                "lucro": lucro,
            })

        resultado = []
        for nome_evento, edicoes in comparativo.items():
            edicoes_ordenadas = sorted(
                edicoes, key=lambda x: x["ano"], reverse=True)
            if len(edicoes_ordenadas) > 1:
                resultado.append(
                    {"evento": nome_evento, "historico": edicoes_ordenadas}
                )

        return resultado

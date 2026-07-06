# utils/forms.py
"""
Formulários da aplicação, utilizando Flask-WTF para validação e proteção
automática contra CSRF.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, TextAreaField, DecimalField, DateField, TimeField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange


class CadastroForm(FlaskForm):
    """Formulário de cadastro de novo usuário (sem biometria nesta etapa)."""
    nome = StringField("Nome completo", validators=[DataRequired(), Length(min=3, max=120)])
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired(), Length(min=6)])
    confirmar_senha = PasswordField(
        "Confirmar senha",
        validators=[DataRequired(), EqualTo("senha", message="As senhas não coincidem.")],
    )


class LoginForm(FlaskForm):
    """Formulário de login (e-mail + senha)."""
    email = StringField("E-mail", validators=[DataRequired(), Email()])
    senha = PasswordField("Senha", validators=[DataRequired()])


class EventoForm(FlaskForm):
    """Formulário de cadastro/edição de eventos (área administrativa)."""
    nome = StringField("Nome do evento", validators=[DataRequired(), Length(max=150)])
    descricao = TextAreaField("Descrição", validators=[DataRequired()])
    local = StringField("Local", validators=[DataRequired()])
    data = DateField("Data", validators=[DataRequired()])
    horario = TimeField("Horário", validators=[DataRequired()])
    valor = DecimalField("Valor (R$)", validators=[DataRequired(), NumberRange(min=0)])
    imagem = FileField("Imagem do evento", validators=[FileAllowed(["jpg", "jpeg", "png"], "Apenas imagens!")])


class BiometriaForm(FlaskForm):
    """Formulário de upload de selfie para cadastro biométrico ou validação de entrada."""
    selfie = FileField(
        "Selfie",
        validators=[FileRequired(message="Selecione uma imagem."), FileAllowed(["jpg", "jpeg", "png"], "Apenas imagens!")],
    )

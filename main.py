from flask import Flask, render_template, request, session, redirect, flash, jsonify
from flask import request
import mysql.connector
from datetime import timedelta, datetime
import plotly.graph_objs as go
import datetime

database_db = {
    'user': 'sql10697011',
    'password': 'RhQccwsMU9',
    'host': 'sql10.freemysqlhosting.net',
    'database': 'sql10697011'
}

app = Flask(__name__)
app.secret_key = "@sd2¨21%d2$#rd1ed12&21@"
app.permanent_session_lifetime = timedelta(days=365)


@app.route('/', methods=['GET', 'POST'])
def index():
    if "user" in session:
        user = session["user"]
        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
        dados_user = cursor.fetchall()

        if dados_user[0][4] == 'administrador':
            cursor.execute("SELECT * FROM tarefas WHERE NOT status = 'arquivada'")
            dados = cursor.fetchall()
        else:
            cursor.execute(
                "SELECT * FROM tarefas WHERE setor = '" + dados_user[0][4] + "' AND status <> 'arquivada'")
            dados = cursor.fetchall()

        cursor.close()

        return render_template("index.html", dados=dados, len_dados=len(dados), nome_user=dados_user[0][2],
                               dados_user=dados_user)
    else:
        return redirect('/login')


@app.route('/alterar_status/<codigo>/<status>', methods=['GET', 'POST'])
def alterar_status(codigo, status):
    if "user" in session:
        user = session["user"]

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT setor FROM tarefas WHERE id = '" + codigo + "'")
        setor_tarefa = cursor.fetchall()[0][0]
        cursor.execute("SELECT setor FROM usuarios WHERE usuario = '" + user + "'")
        setor_usuario = cursor.fetchall()[0][0]

        if setor_tarefa == setor_usuario or setor_usuario == 'administrador':
            sql = "UPDATE tarefas SET status = %s WHERE id = %s"
            val = (status, codigo)
            cursor.execute(sql, val)
            banco.commit()

            if status == "concluida":
                agora = datetime.datetime.now()
                data_hora_formatada = agora.strftime("%Y-%m-%d %H:%M:%S")

                sql = "UPDATE tarefas SET data_finalizado = %s WHERE id = %s"
                val = (data_hora_formatada, codigo)
                cursor.execute(sql, val)
                banco.commit()

            return redirect('/')
        else:
            return "Voce nao e desse setor!"


@app.route('/mensagens/', methods=['GET', 'POST'])
def mensagens():
    if "user" in session:
        user = session["user"]

        if request.method == 'GET':
            codigo = request.args.get('codigo')
        elif request.method == 'POST':
            data = request.json
            codigo = data.get('codigo')

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT * FROM chat WHERE codigo = '" + codigo + "' ORDER BY data_hora DESC")
        conversa = cursor.fetchall()

        return jsonify(conversa)


@app.route('/enviar_mensagem', methods=['GET', 'POST'])
def enviar_mensagem():
    if "user" in session:
        user = session["user"]

        agora = datetime.datetime.now()
        data_hora_formatada = agora.strftime("%Y-%m-%d %H:%M:%S")
        mensagem = request.json.get('mensagem')

        data = request.json
        codigo = data.get('codigo')  # Obtendo o parâmetro 'codigo' do JSON

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT nome FROM usuarios WHERE usuario = '" + user + "'")
        nome_usuario = cursor.fetchall()[0][0]

        cursor.execute("INSERT INTO chat (codigo, usuario, mensagem, data_hora) VALUES (%s, %s,%s, %s)",
                       (codigo, nome_usuario, mensagem, data_hora_formatada))
        banco.commit()
        banco.close()
        return jsonify({'status': 'Mensagem enviada com sucesso'})

    return jsonify({'error': 'Usuário não autenticado'}), 401


@app.route('/login', methods=['GET', 'POST'])
def login():
    banco = mysql.connector.connect(**database_db)
    cursor = banco.cursor()

    if request.method == "POST":
        nome = request.form["usuario"]
        senha_inserida = request.form["senha"]

        try:
            sql = 'SELECT senha FROM usuarios WHERE usuario = %s'
            val = (nome,)
            cursor.execute(sql, val)
            senha_correta_hash = cursor.fetchall()[0][0]

            if senha_correta_hash == senha_inserida:
                session["user"] = nome.lower()
                return redirect('/')
            else:
                flash(u'Sua senha esta incorreta!.', 'error')
        except:
            flash(u'Usuario nao encontrado.', 'error')
    return render_template("login.html")


@app.route('/criar_tarefa', methods=['GET', 'POST'])
def criar_tarefa():
    if "user" in session:
        user = session["user"]

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
        dados = cursor.fetchall()
        setor = dados[0][4]

        if setor == "administrador":
            if request.method == "POST":
                titulo = request.form["titulo"]
                descricao = request.form["descricao"]
                setor = request.form["setor"]
                prioridade = request.form["prioridade"]

                agora = datetime.datetime.now()
                data_hora_formatada = agora.strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute(
                    "INSERT INTO tarefas (remetente, tarefa, setor, descricao,prioridade,status,data_lancamento) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (user, titulo, setor, descricao, prioridade, 'nao_iniciada', data_hora_formatada))
                banco.commit()
                flash(u'Sua tarefa foi criada com sucesso!.', 'sucess')
                return render_template("criar_tarefa.html", dados=dados)
            else:
                return render_template("criar_tarefa.html", dados=dados)
        else:
            flash(u'Apenas administradores podem lancar tarefas!.', 'error')
            return redirect('/')
    else:
        return redirect('/login')


@app.route('/criar_usuario', methods=['GET', 'POST'])
def criar_usuario():
    if "user" in session:
        user = session["user"]

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
        dados = cursor.fetchall()
        setor = dados[0][4]

        if setor == "administrador":
            if request.method == "POST":
                nome = request.form["nome"]
                usuario = request.form["usuario"]
                senha = request.form["senha"]
                confirmar_senha = request.form["confirmar_senha"]
                email = request.form["email"]
                foto_user = request.form["foto_url"]
                setor = request.form["setor"]

                if senha == confirmar_senha:
                    cursor.execute(
                        "INSERT INTO usuarios (nome, usuario, senha, email,foto_user,setor,responsavel) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (nome, usuario, senha, email, foto_user, setor, user))
                    banco.commit()
                    flash(u'Usuario criado com sucesso!', 'sucess')
                else:
                    flash(u'Senha estao diferentes.', 'error')
                return render_template("criar_usuario.html", dados=dados)
            else:
                return render_template("criar_usuario.html", dados=dados)
        else:
            flash(u'Apenas administradores podem criar usuarios!', 'error')
            return redirect('/')
    else:
        return redirect('/login')


@app.route('/configuracao', methods=['GET', 'POST'])
def configuracao():
    if "user" in session:
        user = session["user"]

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        if request.method == "POST":
            cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
            dados = cursor.fetchall()

            email = request.form["email"]
            foto_url = request.form["foto_url"]

            cursor.execute("UPDATE usuarios SET email = '" + email + "' WHERE usuario = '" + user + "'")
            cursor.execute("UPDATE usuarios SET foto_user = '" + foto_url + "' WHERE usuario = '" + user + "'")
            banco.commit()

            flash(u'Seus dados foram alterados.', 'sucess')

            return redirect('/configuracao')
        else:

            cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
            dados = cursor.fetchall()
            return render_template("configuracao.html", dados=dados)
    else:
        return redirect('/login')


@app.route('/usuarios', methods=['GET', 'POST'])
def usuarios():
    if "user" in session:
        user = session["user"]

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
        dados = cursor.fetchall()
        setor = dados[0][4]

        if setor == "administrador":

            cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
            dados_user = cursor.fetchall()
            cursor.execute("SELECT * FROM usuarios")
            dados = cursor.fetchall()

            return render_template('usuarios.html', dados_user=dados_user, dados=dados, len_usuarios=len(dados))
        else:
            flash(u'Apenas administradores podem vizualizar os usuarios!.', 'error')
            return redirect('/')
    else:
        return redirect('/login')


@app.route('/tarefas_arquivadas', methods=['GET', 'POST'])
def tarefas_arquivadas():
    if "user" in session:
        user = session["user"]

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
        dados = cursor.fetchall()
        setor = dados[0][4]

        if setor == "administrador":
            cursor.execute("SELECT * FROM tarefas WHERE status = 'arquivada'")
            dados_tarefas = cursor.fetchall()

            return render_template('arquivadas.html', dados=dados, dados_tarefas=dados_tarefas,
                                   len_dados_tarefas=len(dados_tarefas))
        else:
            flash(u'Apenas administradores podem vizualizar as tarefas arquivadas!.', 'error')
            return redirect('/')
    else:
        return redirect('/login')


@app.route('/dashboard_tarefas', methods=['GET', 'POST'])
def dashboard_tarefas():
    if "user" in session:
        user = session["user"]

        banco = mysql.connector.connect(**database_db)
        cursor = banco.cursor()

        cursor.execute("SELECT * FROM usuarios WHERE usuario = '" + user + "'")
        dados = cursor.fetchall()

        cursor.execute("SELECT * FROM tarefas WHERE status = 'nao_iniciada'")
        nao_iniciada = len(cursor.fetchall())
        cursor.execute("SELECT * FROM tarefas WHERE status = 'em_andamento'")
        em_andamento = len(cursor.fetchall())
        cursor.execute("SELECT * FROM tarefas WHERE status = 'pausada'")
        pausada = len(cursor.fetchall())
        cursor.execute("SELECT * FROM tarefas WHERE status = 'pronta_para_revisao'")
        pronta_para_revisao = len(cursor.fetchall())
        cursor.execute("SELECT * FROM tarefas WHERE status = 'concluida'")
        concluida = len(cursor.fetchall())
        labels = ["Nao iniciada", "Em andamento", "Pausada", "Pronta para Revisao", "Concluida"]
        data = [nao_iniciada, em_andamento, pausada, pronta_para_revisao, concluida]

        cursor.execute("SELECT * FROM tarefas WHERE prioridade = 'alta_prioridade'")
        alta_prioridade = len(cursor.fetchall())
        cursor.execute("SELECT * FROM tarefas WHERE prioridade = 'media_prioridade'")
        media_prioridade = len(cursor.fetchall())
        cursor.execute("SELECT * FROM tarefas WHERE prioridade = 'baixa_prioridade'")
        baixa_prioridade = len(cursor.fetchall())
        cursor.execute("SELECT * FROM tarefas WHERE prioridade = 'prioridade_critica'")
        prioridade_critica = len(cursor.fetchall())
        cursor.execute("SELECT * FROM tarefas WHERE prioridade = 'prioridade_normal'")
        prioridade_normal = len(cursor.fetchall())

        labels2 = ["Alta Prioridade", "Media Prioridade", "Baixa Prioridade", "Prioridade Critica", "Prioridade Normal"]
        data2 = [alta_prioridade, media_prioridade, baixa_prioridade, prioridade_critica, prioridade_normal]

        return render_template('dashboard_tarefas.html', labels=labels, data=data, labels2=labels2, data2=data2,
                               dados=dados)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect('/')


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

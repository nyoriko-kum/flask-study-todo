from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from flask_todo.models import User
from datetime import datetime, date
from flask_todo import db, login_manager
import re

#bpモジュールのインスタンス化
#Blueprintとは機能ごとにファイルを分割し管理しやすくするために利用する機能です
#bluePrintをつかえば、機能ごとにファイルをわけられちゃうんですね！！gakupuruです！
#引数では、todo_appと言う名前で纏めるようにしています。url_prefixには纏めたファイルをurlで纏める事が出来ますが今回は引数無し
#url_prefixを指定すると例；url_prefix="/admin"とかすると/admin/home.htmlや/admin/user.htmlって感じでurlが指定できます。
bp = Blueprint('todo_app', __name__, url_prefix='')

#初期画面はhome.htmlを表示させます
@bp.route('/')
def home():
    return render_template('home.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("todo_app.home"))


@bp.route('/login', methods=['GET', 'POST'])
def login():
    #formからemailとpasswordを取得
    email = request.form.get('email')
    password = request.form.get('password')
    #取得したemailとデータベースのemailが一致するもののパスワードを取得
    if request.method == 'POST':
        #これはオブジェクトになっています。Userテーブルにあるemailが同じやつをクエリしてくれています。
        #なんで、この関数が使えるかというと、select～は、一番最初のimportでＵｓｅｒデータベースとともにmodelsをインポートしています。
        user = User.select_by_email(email)

#取得したパスワードとデータベースのパスワードが等しければログインセッション完了し、ホームを表示
#これは、modelsの中にあるvalidate_passwordを呼び出して自分自身のpasswordにpasswordを代入。
        if user and user.validate_password(password):
            #ユーザーをログイン状態にするための関数:login_user
            #指定されたユーザーオブジェクトをログインセッションに登録し、ログイン状態を保持し、保護されたエンドポイントへのアクセスができるようになる。
            login_user(user)
            #@login_requiredでログイン未完了でもともとリクエストしたページにlogin()できずに遷移してきた場合は、urlは/next=user.htmlとして元々実行したかったURLが格納されちるので、そこに遷移させます。
            next = request.args.get('next')
            if not next:
                #nextがなかった場合のデフォルトの遷移先を指定しています。
                next = url_for('todo_app.user')
            return redirect(next)

#一致しなかった場合には、ログイン画面にもどる。
    return render_template('login.html', last_access=datetime.now())



#ユーザー登録
@bp.route('/register',methods=['GET', 'POST'])
def register():
    #書き込まれた項目を取得する
    #get()の引数は、それぞれinputタグのnameオプションになります
    username = request.form.get('name')
    email = request.form.get('email')
    password1 = request.form.get('password1')
    password2 = request.form.get('password2')

    #メールアドレスの形式を正規表現で想定している
    #任意の文字が一つ以上＋　.は任意の文字
    #^は先頭を指定^は行の先頭を表し、[a-zA-Z0-9_.+-]は、アルファベット（大文字・小文字）、数字、アンダースコア、ピリオド、プラス、ハイフンのいずれか1文字にマッチすることを意味します
    #$は最後を指定
    pattern = "^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"

    #POSTリクエストの場合
    if request.method == 'POST':
        #どこかに空欄がある場合
        if username == '' or email == '' or password1 == '' or password2 == '':
            flash('空のフォームがあります')
        #パスワードが一致しない場合
        elif password1 != password2:
            flash('パスワードが一致しません')
        #メールアドレスの形式になっていない場合
        elif re.match(pattern, email) is None:
            flash('メールアドレスの形式になっていません')
        #すべて正しく入力された場合
        else:
            #書き込まれた項目を取得する
            #全ての項目で正しく入力された場合は、フォームから取得した文字列をインスタンス化した引数に割り当てます
            user = User(
                    email = email,
                    username = username,
                    password = password1
                    )
            #databaseにあるメールアドレスを取得する
            #データベースにメールアドレスが登録されていなければＮｏｎｅになる
            DBuser = User.select_by_email(email)

            #メールアドレスが取得された場合
            if DBuser != None:
                flash('登録済みです')
            #メールアドレスが取得されなかった場合
            else:
                #データベースへの書き込みを行う
                #try-except文は、errorが出る場合を想定して記載する場合に使います。
                #今回の場合は、トランザクションの保証です。データベースに書き込みがうまくいかなかったら、動作を巻き戻す処理が入っています。
                #finally節は、エラーが起ころうが起こらなかろうが、最後に必ず処理する内容を書き込みます。今回はセッションを切るということです。
                try:
                    #データベースとの接続を開始する
                    #with文とは、ファイル操作や通信などの開始時の前処理と終了時の後処理など必須となる処理を自動で実行してくれるものでこれを使わないとファイルオープン、ファイルクローズを書かないといけなくなる。
                    with db.session.begin(subtransactions=True):
                        #データベースに書き込むデータを用意する
                        db.session.add(user)
                        #データベーへの書き込みを実行する
                    db.session.commit()
                    #書き込みがうまくいかない場合
                except:
                    #データベースへの書き込みを行わずにロールバックする
                    db.session.rollback()
                    #raiseでraise eとするとスタックトレース（エラーをトレースする機能）でraise eで再度エラーを送出してしまうので、エラー箇所をトレースしにくい。raiseとするとエラーがそのまま送出されてトレースがそのままになる。
                    raise
                #データベースとの接続を終了する
                finally:
                    db.session.close()
                #成功すればlogin.htmlに遷移する
                return redirect(url_for('todo_app.login'))
    return render_template('register.html')


#ToDoを表示するページを用意
@bp.route('/user')

#@login_requiredは認証されたユーザーだけが表示できるようにするコードです
#login_requiredはflask_loginの機能の一つです。
#このデコレータを特定のビュー関数に適用することで、その特定のルートやエンドポイントにアクセスする際に
#ユーザーがログインしているかどうかを検証し、ログインしていない場合はログインページにリダイレクトするようにします
#ビュー関数が呼び出される前にユーザーのログイン状態をチェックし、ログインしていない場合はログインページにリダイレクトされます
#もしかしたら、実際はuser関数は実行された状態で、それがlogin_requiredにわたされて、ログイン状態を検証しＴｒｕｅなら表示って感じかな？
@login_required
def user():
    return render_template('user.html')




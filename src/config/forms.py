from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired


class ConfigForm(FlaskForm):
    db_host = StringField('数据库主机', validators=[DataRequired()])  # 新增数据库主机字段
    email = StringField('邮箱', validators=[DataRequired()])
    key = StringField('密钥', validators=[DataRequired()])
    quake_token = StringField('Quake 令牌', validators=[DataRequired()])
    db_user = StringField('数据库用户', validators=[DataRequired()])
    db_password = StringField('数据库密码', validators=[DataRequired()])
    db_name = StringField('数据库名称', validators=[DataRequired()])
    submit = SubmitField('提交')

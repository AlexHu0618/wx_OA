# -*- coding: utf-8 -*-
# @Time    : 10/15/19 10:08 AM
# @Author  : Alex Hu
# @Contact : jthu4alex@163.com
# @FileName: models.py
# @Software: PyCharm
# @Blog    : http://www.gzrobot.net/aboutme
# @version : 0.1.0

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Time, Date, Table, MetaData, SmallInteger
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import distinct
import threading
import datetime
import re


Base = declarative_base()


t_map_doctor_patient = Table(
    'map_doctor_patient', Base.metadata,
    Column('doctor_id', Integer, ForeignKey('info_doctor.id')),
    Column('patient_id', Integer, ForeignKey('info_patient.id'))
)


t_map_doctor_questionnaire = Table(
    'map_doctor_questionnaire', Base.metadata,
    Column('doctor_id', Integer, ForeignKey('info_doctor.id')),
    Column('questionnaire_id', Integer, ForeignKey('info_questionnaire.id'))
)


class Hospital(Base):
    __tablename__ = 'info_hospital'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))

    departments = relationship('Department', backref='hospital')
    questionnaires = relationship('Questionnaire', backref='hospitals')


class Department(Base):
    __tablename__ = 'info_department'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    hospital_id = Column(ForeignKey('info_hospital.id'))

    questionnaires = relationship('Questionnaire', backref='departments')


class Doctor(Base):
    __tablename__ = 'info_doctor'

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    department_id = Column(Integer, ForeignKey('info_department.id'))
    hospital_id = Column(Integer)
    medicine_id = Column(Integer)
    role_id = Column(ForeignKey('info_role.id'), index=True)
    nickname = Column(String(20))
    password = Column(String(128))

    department = relationship('Department', backref='doctors')
    role = relationship('Role', primaryjoin='Doctor.role_id == Role.id', backref='info_doctors')


class Role(Base):
    __tablename__ = 'info_role'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))


class Patient(Base):
    __tablename__ = 'info_patient'

    id = Column(Integer, primary_key=True)
    gzh_openid = Column(String(50))
    minip_openid = Column(String(50))
    unionid = Column(String(50), nullable=False, unique=True)
    url_portrait = Column(String(255))
    name = Column(String(20))
    sex = Column(Integer)
    birthday = Column(Date)
    weight = Column(Integer)
    height = Column(Integer)
    nation = Column(String(5))
    email = Column(String(100))
    dt_subscribe = Column(DateTime)
    dt_unsubscribe = Column(DateTime)
    dt_register = Column(DateTime)
    dt_login = Column(DateTime)
    tel = Column(String(20))

    doctors = relationship('Doctor', secondary=t_map_doctor_patient, backref='patients')


class Question(Base):
    __tablename__ = 'info_question'

    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    need_answer = Column(SmallInteger)
    questionnaire_id = Column(ForeignKey('info_questionnaire.id'), nullable=False, index=True)
    qtype = Column(Integer)
    remark = Column(String(200))
    template_id = Column(Integer)

    # options = relationship('Option', back_populates='question')
    options = relationship('Option', backref='question')
    questionnaire = relationship('Questionnaire', primaryjoin='Question.questionnaire_id == Questionnaire.id', backref='info_questions')


class Option(Base):
    __tablename__ = 'info_option'

    id = Column(Integer, primary_key=True)
    question_id = Column(ForeignKey('info_question.id'))
    content = Column(String(200), nullable=False)
    score = Column(Float(8, 3))
    total_votes = Column(Integer)
    goto = Column(Integer)


class QuestionnaireStruct(Base):
    __tablename__ = 'info_questionnaire_struct'

    id = Column(Integer, primary_key=True)
    question_id_list = Column(String(255))
    period = Column(Integer)
    day_start = Column(Integer)
    day_end = Column(Integer)
    interval = Column(Integer)
    respondent = Column(Integer)
    questionnaire_id = Column(ForeignKey('info_questionnaire.id'))
    process_type = Column(Integer)
    title = Column(String(100))
    time = Column(Time)


class Medicine(Base):
    __tablename__ = 'info_medicine'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    questionnaires = relationship('Questionnaire', backref='medicine')


class Questionnaire(Base):
    __tablename__ = 'info_questionnaire'

    id = Column(String(255), primary_key=True)
    title = Column(String(50), nullable=False)
    sub_title = Column(String(50))
    direction = Column(String(50))
    dt_created = Column(DateTime)
    dt_modified = Column(DateTime)
    total_days = Column(Integer)
    medicine_id = Column(ForeignKey('info_medicine.id'))
    result_table_name = Column(String(100))
    hospital_id = Column(ForeignKey('info_hospital.id'))
    department_id = Column(ForeignKey('info_department.id'))
    creator = Column(String(30))
    modifier = Column(String(30))
    code = Column(String(255))
    status = Column(Integer)

    struct = relationship('QuestionnaireStruct', backref='questionnaires')
    doctors = relationship('Doctor', secondary=t_map_doctor_questionnaire, backref='questionnaires')


class MapPatientQuestionnaire(Base):
    __tablename__ = 'map_patient_questionnaire'

    id = Column(Integer, primary_key=True)
    patient_id = Column(ForeignKey('info_patient.id'), unique=True, nullable=False, index=True)
    questionnaire_id = Column(ForeignKey('info_questionnaire.id'), nullable=False, index=True)
    weight = Column(Integer)
    height = Column(Integer)
    age = Column(Integer)
    is_smoking = Column(Integer)
    is_drink = Column(Integer)
    is_operated = Column(Integer)
    total_days = Column(Integer)
    score = Column(Float(8, 3))
    doctor_id = Column(ForeignKey('info_doctor.id'), nullable=False, index=True)
    status = Column(Integer, nullable=False)
    dt_built = Column(DateTime)
    dt_lasttime = Column(DateTime)
    current_period = Column(Integer)
    days_remained = Column(Integer)
    interval = Column(Integer)
    need_send_task_module = Column(String(100), default=None)
    need_answer_module = Column(String(100), default=None)

    doctor = relationship('Doctor', primaryjoin='MapPatientQuestionnaire.doctor_id == Doctor.id',
                          backref='map_patient_questionnaires')
    patients = relationship('Patient', primaryjoin='MapPatientQuestionnaire.patient_id == Patient.id',
                            backref='map_patient_questionnaires')
    questionnaire = relationship('Questionnaire',
                                 primaryjoin='MapPatientQuestionnaire.questionnaire_id == Questionnaire.id',
                                 backref='map_patient_questionnaires')


class DbController(threading.Thread):
    """
    后续改进中，打开线程必须使用装饰器
    """

    conn_pool = create_engine('mysql+pymysql://sa:123456@47.104.179.47/dp_questionnaire_sys?autocommit=true',
                              max_overflow=2,
                              pool_size=5,
                              pool_timeout=30,
                              pool_recycle=-1
                              )
    cursor = sessionmaker(bind=conn_pool)
    session = cursor()
    thrd_counter = 0

    def __init__(self, func, **kwargs):
        super().__init__()
        self.func = func
        self.kwargs = kwargs
        self.thrd_counter = self.thrd_counter + 1
        print('current DbController obj counter is ', self.thrd_counter)

    def __del__(self):
        self.session.close()
        self.thrd_counter = self.thrd_counter - 1
        print('current DbController obj counter is ', self.thrd_counter)

    def run(self):
        if self.func == 'add_user_subscribe':
            if 'unionid' in self.kwargs.keys():
                self.add_user_subscribe(self.kwargs['openid'], self.kwargs['unionid'])
            else:
                print('args error, no unionid')

        elif self.func == 'get_all_remind_time':
            self.get_all_remind_time(self.kwargs['mycache'])
        elif self.func == 'get_specified_remind_openid':
            self.get_specified_remind_openid(self.kwargs['mycache'], self.kwargs['remind_time'])
        elif self.func == 'update_day_oneday':
            self.update_day_oneday()
        elif self.func == 'delete_user_subscribe':
            self.delete_user_subscribe(self.kwargs['openid'])
        else:
            pass

    def add_user_subscribe(self, openid, unionid):
        user_modify = self.session.query(Patient).filter_by(unionid=unionid).one_or_none()
        if user_modify:
            print('the user has been existed')
            try:
                user_modify.dt_subscribe = datetime.datetime.now()
                user_modify.db_unsubscribe = None
                user_modify.gzh_openid = openid
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(e)
        else:
            user = Patient(gzh_openid=openid, unionid=unionid, dt_subscribe=datetime.datetime.now())
            try:
                self.session.add(user)
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(e)

    def delete_user_subscribe(self, openid):
        user_modify = self.session.query(Patient).filter_by(gzh_openid=openid).one_or_none()
        if user_modify:
            try:
                user_modify.dt_subscribe = None
                user_modify.db_unsubscribe = datetime.datetime.now()
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(e)
        else:
            print('there is no user: ', openid)

    def get_all_remind_time(self, mycache):
        all_time = self.session.query(distinct(QuestionnaireStruct.time)).filter_by(respondent=0).all()
        all_time_sorted = sorted([i[0] for i in all_time])
        mycache.set('all_remind_time', all_time_sorted)
        print(all_time_sorted)

    def get_specified_remind_openid(self, mycache, remind_time):
        ######################################
        ## get all patient for reminding
        #####################################
        rsl = self.session.query(QuestionnaireStruct.id, QuestionnaireStruct.questionnaire_id,
                                 QuestionnaireStruct.period).filter_by(time=remind_time, respondent=0).all()
        openid_set = set()
        print(rsl)
        if rsl:  ## [(id, questionnnaire_id, period), ...]
            for i in rsl:
                rsl_mappqn = self.session.query(MapPatientQuestionnaire).filter_by(questionnaire_id=i[1],
                                                                                   current_period=i[2],
                                                                                   status=1).all()
                print(rsl_mappqn)
                if rsl_mappqn:
                    pid_list = [r.patient_id for r in rsl_mappqn]
                    rsl_single = self.session.query(Patient.gzh_openid, Patient.id).filter(Patient.id.in_(pid_list)).all()
                    print(rsl_single)
                    if rsl_single:
                        set_single_qn = set([j[0] for j in rsl_single])
                        openid_set = openid_set | set_single_qn
                        for r in rsl_mappqn:
                            print(r)
                            if r.need_answer_module:
                                module_list = re.split(',', r.need_answer_module).append(str(i[0]))
                                module_list2str = ','.join(module_list)
                                r.need_answer_module = module_list2str
                            else:
                                r.need_answer_module = str(i[0])
                    else:
                        print('there is no record')
                else:
                    print('warning! mapPatientQuestionnaire--%s is None', i[1])
            try:
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(e)
        else:
            print('warning! there is no openid for the remind time-- ', remind_time)
        mycache.set('remind_openid_set', openid_set)

    def update_day_oneday(self):
        rsl = self.session.query(MapPatientQuestionnaire).filter(MapPatientQuestionnaire.status == 1).all()
        if rsl:
            for i in rsl:
                if i.days_remained == 1:
                    ## current period is end
                    rsl_s = self.session.query(QuestionnaireStruct).filter(
                        QuestionnaireStruct.questionnaire_id == i.questionnaire_id,
                        QuestionnaireStruct.respondent == 0,
                        QuestionnaireStruct.period == i.current_period + 1).one_or_none()
                    if rsl_s:
                        i.current_period = i.current_period + 1
                        i.days_remained = rsl_s.day_end - rsl_s.day_start + 1
                        i.interval = rsl_s.interval
                        i.need_answer_module = None
                    else:
                        print('there is no recode for update_day_oneday()')
                else:
                    i.days_remained = i.days_remained - 1
                    i.need_answer_module = None
            try:
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(e)
        else:
            print('there is no MapPatientQuestionnaire for update_day_oneday()')

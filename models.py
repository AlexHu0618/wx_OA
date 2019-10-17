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
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Time
from sqlalchemy.orm import relationship, backref
from sqlalchemy.orm import sessionmaker
from sqlalchemy import distinct
import threading

Base = declarative_base()


class Role(Base):
    __tablename__ = 'info_role'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))


class Doctor(Base):
    __tablename__ = 'info_doctor'

    id = Column(Integer, primary_key=True)
    name = Column(String(30))
    department_id = Column(Integer)
    hospital_id = Column(Integer)
    medicine = Column(String(50))
    role_id = Column(ForeignKey('info_role.id'), index=True)
    nickname = Column(String(20))
    password = Column(String(128))


class Patient(Base):
    __tablename__ = 'info_patient'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))
    sex = Column(Integer)
    age = Column(Integer)
    nation = Column(String(5))
    weight = Column(Float(8, 2))
    height = Column(Integer)
    year_smoking = Column(Integer)
    year_drink = Column(Integer)
    tel = Column(String(20))
    dt_register = Column(DateTime)
    dt_login = Column(DateTime)
    wechat_openid = Column(String(30))
    dt_subscribe = Column(DateTime)
    dt_unsubscribe = Column(DateTime)


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
    is_release = Column(Integer)

    struct = relationship('QuestionnaireStruct', backref=backref('questionnaires'))


class MapPatientQuestionnaire(Base):
    __tablename__ = 'map_patient_questionnaire'

    id = Column(Integer, primary_key=True)
    patient_id = Column(ForeignKey('info_patient.id'), nullable=False, index=True)
    questionnaire_id = Column(ForeignKey('info_questionnaire.id'), nullable=False, index=True)
    total_days = Column(Integer)
    score = Column(Float(8, 2))
    doctor_id = Column(ForeignKey('info_doctor.id'), nullable=False, index=True)
    register_state = Column(Integer, nullable=False)
    dt_built = Column(DateTime)
    dt_lasttime = Column(DateTime)
    current_period = Column(Integer)
    days_remained = Column(Integer)
    interval = Column(Integer)

    doctor = relationship('Doctor', primaryjoin='MapPatientQuestionnaire.doctor_id == Doctor.id',
                          backref=backref('map_patient_questionnaires'))
    patients = relationship('Patient', primaryjoin='MapPatientQuestionnaire.patient_id == Patient.id',
                            backref=backref('map_patient_questionnaires'))
    questionnaire = relationship('Questionnaire',
                                 primaryjoin='MapPatientQuestionnaire.questionnaire_id == Questionnaire.id',
                                 backref=backref('map_patient_questionnaires'))


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
            if 'openid' in self.kwargs.keys():
                self.add_user_subscribe(self.kwargs['openid'])
            else:
                print('args error, no openid')

        elif self.func == 'get_all_remind_time':
            self.get_all_remind_time(self.kwargs['mycache'])
        elif self.func == 'get_specified_remind_openid':
            self.get_specified_remind_openid(self.kwargs['mycache'], self.kwargs['remind_time'])
        else:
            pass

    def add_user_subscribe(self, openid):
        user_modify = self.session.query(Patient).filter_by(wechat_openid=openid).all()
        if user_modify:
            print('the user has been existed')
        else:
            user = Patient(wechat_openid=openid)
            self.session.add(user)
            self.session.commit()

    def get_all_remind_time(self, mycache):
        all_time = self.session.query(distinct(QuestionnaireStruct.time)).filter_by(respondent=0).all()
        all_time_sorted = sorted([i[0] for i in all_time])
        mycache.set('all_remind_time', all_time_sorted)
        print(all_time_sorted)

    def get_specified_remind_openid(self, mycache, remind_time):
        rsl = self.session.query(QuestionnaireStruct.questionnaire_id,
                                 QuestionnaireStruct.period).filter_by(time=remind_time, respondent=0).all()
        openid_set = set()
        print(rsl)
        if rsl:
            for i in rsl:
                rsl_single = self.session.query(Patient.wechat_openid).filter(Patient.id.in_(
                    self.session.query(MapPatientQuestionnaire.patient_id).filter_by(questionnaire_id=i[0],
                                                                                     current_period=i[1]))).all()
                print(rsl_single)
                if rsl_single:
                    set_single_qn = set([i[0] for i in rsl_single])
                    openid_set = openid_set | set_single_qn
                else:
                    print('warning! questionnaire--%s is None', i[0])
        else:
            print('warning! there is no openid for the remind time-- ', remind_time)
        mycache.set('remind_openid_set', openid_set)

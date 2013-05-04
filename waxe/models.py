from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    ForeignKey,
    Table
    )

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
    )

from zope.sqlalchemy import ZopeTransactionExtension
from sqla_declarative import extended_declarative_base

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = extended_declarative_base(DBSession)


user_role = Table(
    'user_role',
    Base.metadata,
    Column('iduser', Integer, ForeignKey('user.iduser')),
    Column('idrole', Integer, ForeignKey('role.idrole')),
)


user_group = Table(
    'user_group',
    Base.metadata,
    Column('iduser', Integer, ForeignKey('user.iduser')),
    Column('idgroup', Integer, ForeignKey('groups.idgroup')),
)


class Group(Base):
    __tablename__ = 'groups'

    idgroup = Column(Integer,
                     nullable=False,
                     autoincrement=True,
                     primary_key=True)
    name = Column(String(255),
                  nullable=False)


class Role(Base):

    idrole = Column(Integer,
                    nullable=False,
                    autoincrement=True,
                    primary_key=True)
    name = Column(String(255),
                  nullable=False)


class User(Base):

    iduser = Column(Integer,
                    nullable=False,
                    autoincrement=True,
                    primary_key=True)
    login = Column(String(255),
                   nullable=False)
    password = Column(String(255),
                      nullable=False)
    idconfig = Column(Integer,
                      ForeignKey('user_config.idconfig'),
                      nullable=True)

    roles = relationship('Role',
                         secondary=user_role,
                         backref='users')
    groups = relationship('Group',
                          secondary=user_group,
                          backref='users')
    config = relationship('UserConfig',
                          backref=backref("user", uselist=False))


class UserConfig(Base):
    __tablename__ = 'user_config'

    idconfig = Column(Integer,
                      nullable=False,
                      primary_key=True)
    root_path = Column(String(255),
                       nullable=False)

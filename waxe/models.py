import os
from sqlalchemy import (
    Column,
    Integer,
    Text,
    String,
    ForeignKey,
    Table,
    Boolean,
)

from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    backref
)

from zope.sqlalchemy import ZopeTransactionExtension
from sqla_declarative import extended_declarative_base
import tw2.sqla as tws
import tw2.forms as twf

from .validator import BCryptValidator

DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = extended_declarative_base(DBSession)

ROLE_ADMIN = 'admin'
ROLE_EDITOR = 'editor'
ROLE_CONTRIBUTOR = 'contributor'

VERSIONING_PATH_STATUS_ALLOWED = 'allowed'
VERSIONING_PATH_STATUS_FORBIDDEN = 'forbidden'


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

    def __unicode__(self):
        return self.name


class User(Base):

    iduser = Column(Integer,
                    nullable=False,
                    autoincrement=True,
                    primary_key=True)
    login = Column(String(255),
                   nullable=False)
    password = Column(String(255),
                      nullable=True,
                      info={'edit_widget':
                            twf.PasswordField(validator=BCryptValidator),
                            'view_widget': tws.NoWidget,
                           }
                     )
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
    versioning_paths = relationship('VersioningPath',
                                    info={'view_widget':
                                          tws.FactoryWidget(separator='<br />')},
                                    backref=backref("user", uselist=False))

    def __unicode__(self):
        return self.login

    def has_role(self, name):
        for role in self.roles:
            if role.name == name:
                return True
        return False

    def is_admin(self):
        return self.has_role(ROLE_ADMIN)

    def can_commit(self, path):
        if not os.path.exists(path):
            raise Exception('Invalid path %s' % path)

        if self.has_role(ROLE_ADMIN):
            return True

        if self.has_role(ROLE_EDITOR):
            return True

        assert self.has_role(ROLE_CONTRIBUTOR), 'You are not a contributor'

        if os.path.isfile(path):
            path = os.path.dirname(path)

        path = os.path.normpath(path)

        paths = list(self.versioning_paths)
        paths.sort(lambda a, b: cmp(len(a.path), len(b.path)))
        paths.reverse()
        for p in paths:
            if path.startswith(os.path.normpath(p.path)):
                if VERSIONING_PATH_STATUS_ALLOWED == p.status:
                    return True
                return False
        return False


class UserConfig(Base):
    __tablename__ = 'user_config'

    idconfig = Column(Integer,
                      nullable=False,
                      primary_key=True)
    root_path = Column(String(255),
                       nullable=False)
    use_versioning = Column(Boolean, nullable=False, default=False)

    versioning_password = Column(
        String(255),
        nullable=True,
        info={'edit_widget':
              twf.PasswordField,
              'view_widget': tws.NoWidget}
    )

    def get_tws_view_html(self):
        return 'path: %s <br /> Versioning: %s' % (self.root_path,
                                             self.use_versioning)


class VersioningPath(Base):
    __tablename__ = 'versioning_path'

    idversioning_path = Column(Integer, nullable=False, primary_key=True)
    iduser = Column(Integer, ForeignKey('user.iduser'))
    status = Column(String(255), nullable=False)
    path = Column(String(255), nullable=False)

    def __unicode__(self):
        return '%s: %s' % (self.status, self.path)


def get_editors():
    role = DBSession.query(Role).filter_by(name=ROLE_EDITOR).one()
    return [u for u in role.users if u.config and u.config.root_path]


def get_contributors():
    role = DBSession.query(Role).filter_by(name=ROLE_CONTRIBUTOR).one()
    return [u for u in role.users if u.config and u.config.root_path]

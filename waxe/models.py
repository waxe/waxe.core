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
    versioning_paths = relationship('VersioningPath',
                                    backref=backref("user", uselist=False))

    def has_role(self, name):
        for role in self.roles:
            if role.name == name:
                return True
        return False

    def multiple_account(self):
        editors = get_editors()
        contributors = get_contributors()
        if self.has_role(ROLE_ADMIN):
            if editors or contributors:
                return True
        if self.has_role(ROLE_EDITOR):
            if contributors:
                return True
        return False

    def get_editable_logins(self, exclude=None):
        lis = []
        if self.config and self.config.root_path:
            lis += [self.login]

        editors = get_editors()
        contributors = get_contributors()
        if self.has_role(ROLE_ADMIN):
            for user in (editors + contributors):
                lis += [user.login]
        elif self.has_role(ROLE_EDITOR):
            for user in contributors:
                lis += [user.login]

        if exclude:
            return [l for l in lis if l != exclude]
        return lis

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


class VersioningPath(Base):
    __tablename__ = 'versioning_path'

    idversioning_path = Column(Integer, nullable=False, primary_key=True)
    iduser = Column(Integer, ForeignKey('user.iduser'))
    status = Column(String(255), nullable=False)
    path = Column(String(255), nullable=False)


def get_editors():
    role = DBSession.query(Role).filter_by(name=ROLE_EDITOR).one()
    return [u for u in role.users if u.config and u.config.root_path]


def get_contributors():
    role = DBSession.query(Role).filter_by(name=ROLE_CONTRIBUTOR).one()
    return [u for u in role.users if u.config and u.config.root_path]

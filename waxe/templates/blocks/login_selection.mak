% for login in logins:
  <a href="${request.route_path('login_selection', _query=[('login', login)])}">${login}</a>
% endfor

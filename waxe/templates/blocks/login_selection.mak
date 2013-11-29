Please select the account you want to use:
<br />
<br />
<ul class="list-unstyled">
% for login in logins:
  <li>
    <a href="${request.route_path('login_selection', _query=[('login', login)])}">${login}</a>
  </li>
% endfor
</ul>

Please the account you want to use:
<br />
<br />
% for login in logins:
  <ul class="list-unstyled">
	<li>
	  <a href="${request.route_path('login_selection', _query=[('login', login)])}">${login}</a>
	</li>
  </ul>
% endfor

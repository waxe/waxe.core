<div class="row" style="margin-right: 0; margin-left: 0;">
<div class="col-md-8">
Please select the account you want to use:
<br />
<br />
<ul class="list-unstyled">
% for login in logins:
  <li>
    <a href="${request.route_path('home', login=login, _query=qs)}">${login}</a>
  </li>
% endfor
</ul>
</div>
% if last_files:
<div class="col-md-4">
  ${last_files|n}
</div>
% endif
</div>

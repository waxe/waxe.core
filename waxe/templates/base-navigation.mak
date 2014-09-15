<%inherit file="base.mak" />
<body style="padding-top: 85px;">
  <header>
  <nav class="navbar navbar-default navbar-fixed-top">
    <div class="navbar-header">
        <a class="navbar-brand" href="${request.route_path('redirect')}">WAXE</a>
      </div>

    <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
        <ul class="nav navbar-nav">
          <li><a class="new" title="New" data-href="${request.custom_route_path('new_json')}" href="#">New</a></li>
          <li><a class="open" title="Open" data-call="navbar.open" data-fb-href="${request.custom_route_path('open_json')}" href="#">Open</a></li>
          <li><a class="save" title="Save" data-call="navbar.save" href="#">Save</a></li>
          <li><a class="saveas" title="Save as" data-call="navbar.saveas" data-fb-href="${request.custom_route_path('open_json')}" data-fb-folder-href="${request.custom_route_path('create_folder_json')}" href="#">Save as</a></li>
          <li><a class="split" title="Split view" data-call="navbar.split" data-href="${request.custom_route_path('edit')}" href="#">Split view</a></li>

          % if versioning:
          <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">
            Versioning
                <b class="caret"></b>
            </a>
            <ul class="dropdown-menu dropdown-versioning">
                <li>
                  <a href="${request.custom_route_path('versioning_status')}" data-href="${request.custom_route_path('versioning_status_json')}">Status</a>
                </i>
                <li>
                  <a href="${request.custom_route_path('versioning_update')}" data-href="${request.custom_route_path('versioning_update_json')}">Update</a>
                </li>
            </ul>
            </li>
          % endif
          % if search:
            <form class="navbar-form navbar-left" role="search" action="${request.custom_route_path('search')}" data-action="${request.custom_route_path('search_json')}">
              <div class="form-group">
                <input type="text" name="search" class="form-control" placeholder="Search">
              </div>
              <button type="submit" class="btn btn-default">Submit</button>
            </form>
          % endif
        </ul>
        <ul class="nav navbar-nav navbar-right">
          % if logins:
            <li class="dropdown">
              <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                ${editor_login}
                <b class="caret"></b>
              </a>
              <ul class="dropdown-menu">
                % for login in logins:
                  <li>
                  <a href="${request.route_path('home', login=login)}">${login}</a>
                  </li>
                % endfor
              </ul>
            </li>
      % else:
        <li><a>${editor_login}</a></li>
          % endif
      <li><a style="margin-right: 10px;" class="glyphicon glyphicon-log-out" title="Logout" href="${request.route_path('logout')}"></a></li>
        </ul>
      </div>
  </nav>
  </header>

  ${next.body()}
</body>

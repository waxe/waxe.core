<%inherit file="base.mak" />
<body style="padding-top: 95px;">
  <header>
  <nav class="navbar navbar-default navbar-fixed-top">
    <div class="navbar-header">
        <a class="navbar-brand" href="${request.route_path('redirect')}">WAXE</a>
      </div>

    <div class="collapse navbar-collapse">
        <ul class="nav navbar-nav">
          <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">
              File
              <b class="caret"></b>
            </a>
            <ul class="dropdown-menu">
              <li><i class="fa fa-file-o"></i><a title="New" data-href="${request.custom_route_path('new_json')}" href="#">New</a></li>
              % if root_template_path:
                <li><i class="fa fa-file-excel-o"></i><a title="New from template" data-href="${request.custom_route_path('open_template_json')}" href="#">New (template)</a></li>
              % endif
              <li><i class="fa fa-folder-open-o"></i><a title="Open" data-href="${request.custom_route_path('open_json')}" href="#">Open</a></li>
              <li class="disabled"><i class="fa fa-save"></i><a title="Save" class="save" data-call="navbar.save" href="#">Save</a></li>
              <li><i class="fa fa-save"></i><a class="saveas" title="Save as" data-href="${request.custom_route_path('saveas_json')}" href="#">Save as</a></li>
              <li><i class="fa fa-minus"></i><a class="split" title="Split view" data-call="navbar.split" data-href="${request.custom_route_path('edit')}" href="#">Split view</a></li>
            </ul>
          </li>
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
            <form class="navbar-form navbar-left" role="search" action="${request.custom_route_path('search')}" data-action="${request.custom_route_path('search_json')}" method="POST">
              <div class="form-group">
                <input type="text" name="search" class="form-control" placeholder="Search">
              </div>
              <button type="submit" class="btn btn-default">Submit</button>
            </form>
          % endif
        </ul>
        <ul class="nav navbar-nav navbar-right">
          <li class="dropdown">
            <a href="#" class="dropdown-toggle" data-toggle="dropdown">
              ${editor_login}
              <b class="caret"></b>
            </a>
            <ul class="dropdown-menu">
              % if logins:
                % for login in logins:
                  <li>
                  <a href="${request.route_path('home', login=login)}">${login}</a>
                  </li>
                % endfor
              % endif
              <li><i class="fa fa-sign-out"></i><a title="Logout" href="${request.route_path('logout')}">Logout</a></li>
            </ul>
          </li>
        </ul>
      </div>
      <ul class="nav navbar-nav navbar-icons">
        <li><a class="fa fa-file-o" title="New" data-href="${request.custom_route_path('new_json')}" href="#"></a></li>
        <li><a class="fa fa-folder-open-o" title="Open" data-href="${request.custom_route_path('open_json')}" href="#"></a></li>
        <li><a class="save fa fa-save" title="Save" data-call="navbar.save" href="#"></a></li>
      </ul>
  </nav>
  </header>

  ${next.body()}
</body>

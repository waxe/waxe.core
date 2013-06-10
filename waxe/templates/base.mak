<!DOCTYPE html>
<head>
  <title>Waxe</title>
  <meta http-equiv="Content-Type" content="text/html;charset=UTF-8"/>
  <link rel="stylesheet" type="text/css" href="/static/bootstrap/css/bootstrap.css" />
  <link rel="stylesheet" type="text/css" href="/static/css/style.css" />
  <style>
  .navfile .selected{
      background-color: #D9EDF7;
    }
    .navfile li a{
    padding-left: 5px;
    }
  </style>
  <script type="text/javascript" src="/static/js/jquery-1.8.2.min.js"></script>
  <script type="text/javascript" src="/static/js/jquery-ui-1.10.1.custom.min.js"></script>
  <script type="text/javascript" src="/static/bootstrap/js/bootstrap.js"></script>
  <script type="text/javascript" src="/static/js/jquery.layout-latest.min.js"></script>
  <script type="text/javascript" src="/static/js/jquery.jstree.js"></script>
  <script type="text/javascript" src="/static/js/jquery.message.js"></script>
  <script type="text/javascript" src="/static/js/jquery.filebrowser.js"></script>
  <script type="text/javascript" src="/static/js/jquery.autosize.js"></script>
  <script type="text/javascript" src="/static/js/jquery.togglefieldset.js"></script>
  <script type="text/javascript" src="/static/js/xmltool.js"></script>
  <script type="text/javascript" src="/static/js/waxe.js"></script>
</head>
<body style="padding-top: 76px;">
  <header>
    <div class="navbar navbar-inverse navbar-fixed-top">
      <div class="navbar-inner">
        <div class="container">
          <a class="brand" href="#">WAXE</a>
          <ul class="nav">
            <li><a class="new" title="New" data-href="/new.json" href="#">New</a></li>
            <li><a class="open" title="Open" href="#">Open</a></li>
            <li><a class="save" title="Save" href="#">Save</a></li>
            <li><a class="saveas" title="Save as" href="#">Save as</a></li>
            % if logins:
              <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                  ${editor_login}
                  <b class="caret"></b>
                </a>
                <ul class="dropdown-menu">
                  % for login in logins:
                    <li>
                    <a href="${request.route_path('login_selection', _query=[('login', login)])}">${login}</a>
                    </li>
                  % endfor
                </ul>
              </li>
            % endif
            % if versioning:
              <li class="dropdown">
                <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                  Versioning
                  <b class="caret"></b>
                </a>
                <ul class="dropdown-menu dropdown-versioning">
                    <li>
                      <a data-href="${request.route_path('svn_status_json')}">Status</a>
                    </i>
                    <li>
                      <a data-href="${request.route_path('svn_update_json')}">Update</a>
                    </li>
                </ul>
              </li>
            % endif
          </ul>
        </div>
      </div>
    </div>
  </header>

  ${next.body()}

</body>
</html>

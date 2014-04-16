<%inherit file="base.mak" />
<body>
<div class="ui-layout-center">
  <div class="alert alert-danger">
    This form is in readonly and doesn't reload automatically.
    <a onclick="location.reload(); return false;" href="#">Click here to reload it</a>
  </div>
  <form id="xmltool-form">
    ${content|n}
  </div>
  </div>
<div class="ui-layout-east">
  <div id="tree-container">
    <div id="tree">Tree</div>
  </div>
</div>

% if jstree_data:
  <script>
	  var jstree_data = ${jstree_data|n};
  </script>
% endif

</body>

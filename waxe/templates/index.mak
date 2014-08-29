<%inherit file="base-navigation.mak" />

<ul class="breadcrumb navbar-fixed-top" style="top: 55px; z-index: 999; background-color: transparent; margin-bottom: 0px; padding-top: 4px; padding-bottom: 2px;">
% if breadcrumb:
  ${breadcrumb|n}
% endif
</ul>

<div class="ui-layout-center">
  <div class="content">
	% if error_msg:
	<div class="alert alert-danger">
	  ${error_msg|n}
	</div>
	% endif

	% if info_msg:
	<div class="alert alert-info">
	  ${info_msg|n}
	</div>
	% endif

    % if content:
	    ${content|n}
	  % endif
  </div>
</div>

<div class="ui-layout-west">
  <div id="tree-container">
    <div id="tree">Tree</div>
  </div>
</div>

<div class="ui-layout-south">
</div>

% if jstree_data:
  <script>
	  var jstree_data = ${jstree_data|n};
  </script>
% endif

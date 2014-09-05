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

<div class="ui-layout-${layout_tree_position}">
  <div id="tree-container">
    <div id="tree"></div>
  </div>
</div>

<div class="ui-layout-${layout_readonly_position}"></div>

% if jstree_data:
  <script>
	  var jstree_data = ${jstree_data|n};
  </script>
% endif

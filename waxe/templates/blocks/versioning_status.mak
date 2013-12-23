% if conflicteds:
	<p>List of conflicted files that should be resolved:</p>

	<ul class="list-unstyled">
	% for conflicted in conflicteds:
	  <li>
		<span class="label label-${conflicted.status}">${conflicted.status}</span>
		<a href="${request.custom_route_path('edit', _query=[('path', conflicted.relpath)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', conflicted.relpath)])}">${conflicted.relpath}</a>
	  </li>
    % endfor
	</ul>
	<br />
% endif

% if others:
	<p>List of updated files:</p>

	<ul class="list-unstyled">

	% for other in others:
	  <li>
		<span class="label label-${other.status}">${other.status}</span>
		<a href="${request.custom_route_path('edit', _query=[('path', other.relpath)])}" data-href="${request.custom_route_path('edit_json', _query=[('path', other.relpath)])}">${other.relpath}</a>
	  </li>
    % endfor
	</ul>
% endif

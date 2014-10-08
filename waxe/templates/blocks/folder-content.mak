% if previous:
  <i class="fa fa-folder-o"></i>
  ${previous_tag|n}
% endif
<div class="row">
  % for l, r in tags:
    <div class="col-md-6">
      <i class="fa fa-${l[0]}-o"></i>
      ${l[1]|n}
    </div>
    % if r:
    <div class="col-md-6">
      <i class="fa fa-${r[0]}-o"></i>
      ${r[1]|n}
    </div>
    % endif
  % endfor
</div>

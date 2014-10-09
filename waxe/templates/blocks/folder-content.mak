<div class="file-navigation">
% if previous:
  <i class="fa fa-folder-o"></i>
  ${previous_tag|n}
% endif
<div class="row">
  % for l, r in tags:
    <div class="col-md-6">
      ${l[1]|n}
    </div>
    % if r:
    <div class="col-md-6">
      ${r[1]|n}
    </div>
    % endif
  % endfor
</div>
</div>

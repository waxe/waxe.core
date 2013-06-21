<div class="ui-layout-center">
% if files_data:
  <ul>
  % for status, label_class, f, link, json_link in files_data:
    <li>
      <span class="label ${label_class}">${status}</span>
      <a href="${link}" data-href="${json_link}">${f}</a>
    </li>
  % endfor
  </ul>
% endif
</div>

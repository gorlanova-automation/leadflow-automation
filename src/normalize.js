// Pure validation. No secrets, network requests or model-controlled fields.
const raw = $json.body ?? $json;
const text = (key, max) => typeof raw[key] === 'string' ? raw[key].trim().slice(0, max + 1) : '';
const data = {
  request_id: text('request_id',80), name:text('name',80), email:text('email',160).toLowerCase(),
  phone:text('phone',40), message:text('message',2000), source:text('source',40)||'Учебная форма',
  demo:raw.demo===true||raw.demo==='true', category_id:17
};
const errors=[];
if(!/^[A-Za-z0-9_-]{8,80}$/.test(data.request_id)) errors.push('Номер обращения: 8–80 латинских букв, цифр, _ или -');
if(data.name.length<2||data.name.length>80) errors.push('Имя: 2–80 символов');
if(!/^[a-z0-9._%+-]+@example\.com$/.test(data.email)||data.email.length>160) errors.push('Почта: только вымышленный адрес @example.com');
if(data.phone && !/^\+?[0-9 ()-]{6,40}$/.test(data.phone)) errors.push('Телефон: неверный формат');
if(data.message.length<5||data.message.length>2000) errors.push('Сообщение: 5–2000 символов');
if(data.source.length>40) errors.push('Источник: максимум 40 символов');
if(!data.demo) errors.push('Разрешён только учебный режим');
return [{json:{valid:errors.length===0,errors,data,code:errors.length?422:200}}];

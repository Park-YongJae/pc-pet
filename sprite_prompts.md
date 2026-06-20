# PC-PET 스프라이트 생성 프롬프트

## 공통 설정 (Leonardo.ai)
- **Model**: Anime Pastel Dream 또는 Illustrative Albedo
- **Canvas**: 240×280px
- **배경**: 투명 (Remove Background 후 저장)
- **포즈**: 정면 서 있는 자세, 전신

**공통 Negative Prompt**
```
realistic, 3d render, blurry, multiple characters, side view, back view,
cropped, text, watermark, logo, shadow, white background, gray background
```

---

## 귀여운 (Cute)

### 1. 냥이
**파일명**: `pet1_idle.png`

```
chibi orange tabby cat, game sprite, standing front view, full body,
chubby round body, bright orange fur with darker orange stripes,
small triangle ears with pink inner ear, big shiny black eyes with white highlight,
tiny pink nose, small whiskers, round belly with lighter orange patch,
stubby little legs and paws, cute friendly expression,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

### 2. 멍이
**파일명**: `pet2_idle.png`

```
chibi cream golden retriever puppy, game sprite, standing front view, full body,
chubby round body, soft cream colored fur, long floppy droopy ears,
big shiny black eyes with white highlight, tiny black nose,
small red collar with a round tag around neck,
round fluffy tail curled upward, stubby little legs,
cute happy expression with tongue slightly out,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

### 3. 햄토리
**파일명**: `pet3_idle.png`

```
chibi hamster, game sprite, standing front view, full body,
very chubby round body, warm beige and brown fur,
small round ears, big shiny black eyes with white highlight,
extremely puffy chubby cheeks stuffed with food,
tiny pink nose, small stubby arms held out slightly,
round plump body with lighter cream belly,
cute chubby expression,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

### 4. 삐약이
**파일명**: `pet4_idle.png`

```
chibi baby chick, game sprite, standing front view, full body,
fluffy round yellow body covered in soft down feathers,
tiny orange triangular beak, big round shiny black eyes with white highlight,
small stubby yellow wings on sides, tiny orange feet,
small fluffy tail feathers, no ears,
super cute innocent baby expression,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

## 멋진 (Cool)

### 5. 드래곤
**파일명**: `pet5_idle.png`

```
chibi blue dragon, game sprite, standing front view, full body,
small chubby body with steel blue and navy scales,
two short curved horns on head, big expressive yellow eyes with slit pupils,
small folded wings on back, spiky tail with arrow tip,
lighter blue belly scales, tiny sharp claws,
cool confident expression, slightly smug smile,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

### 6. 로봇
**파일명**: `pet6_idle.png`

```
chibi robot, game sprite, standing front view, full body,
boxy rounded metallic silver body with slight sheen,
square head with rounded corners, single antenna on top with blinking light,
two round glowing LED eyes in cyan blue color,
chest panel with small buttons and a tiny heart screen,
short stubby mechanical arms and legs,
bolts and panel lines as details, cool futuristic look,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

### 7. 악마
**파일명**: `pet7_idle.png`

```
chibi devil, game sprite, standing front view, full body,
small chubby crimson red body, two sharp curved devil horns on head,
bat-shaped small wings on back, pointed tail with heart tip,
mischievous glowing yellow eyes with slight frown,
tiny fangs visible in smirk, dark red shadowed belly,
edgy cool expression, arms crossed or one hand on hip,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

## 예쁜 (Pretty)

### 8. 유니콘
**파일명**: `pet8_idle.png`

```
chibi unicorn, game sprite, standing front view, full body,
soft pastel pink and white chubby body,
single spiral golden horn on forehead,
flowing pastel rainbow mane in pink lavender and mint colors,
big sparkly purple eyes with long eyelashes and white highlight,
small hooves, fluffy pastel tail,
magical star sparkles floating around, elegant gentle expression,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

### 9. 천사냥
**파일명**: `pet9_idle.png`

```
chibi angel cat, game sprite, standing front view, full body,
soft white fluffy chubby body, small triangle cat ears,
pair of small feathery white angel wings on back,
golden glowing halo floating above head,
big gentle sparkling blue eyes with white highlight,
tiny pink nose, peaceful serene smile,
subtle golden sparkle effects around body,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

### 10. 요정
**파일명**: `pet10_idle.png`

```
chibi forest fairy, game sprite, standing front view, full body,
small chubby body in soft mint and lime green tones,
pointed elf ears on the sides of head,
delicate translucent dragonfly wings on back,
small flower crown with pink and white flowers on head,
big bright green eyes with white highlight, rosy cheeks,
holding a tiny glowing orb in one hand, playful cheerful expression,
transparent background, flat 2D cartoon illustration, clean black lineart,
no shadow, centered, 240x280 pixels
```

---

## 사용 팁

1. **레퍼런스 고정**: 첫 번째로 마음에 드는 캐릭터 생성 후 `Image Guidance`에 업로드해서 스타일 통일
2. **배경 제거**: Leonardo.ai의 `Remove Background` 기능 사용 후 저장
3. **저장 위치**: `assets/sprites/pet{N}_idle.png`
4. **애니메이션 추가 시**: 동일 프롬프트에 포즈만 바꿔서 생성 (`walking pose`, `eating pose` 등)

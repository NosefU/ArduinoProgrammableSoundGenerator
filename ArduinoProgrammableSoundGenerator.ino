#include "APSG.h"
#include "melodies.h"
#include "GyverHacks.h"

//                                       C    C#     D    D#     E     F    F#     G    G#     A    A#     B          octave
const static uint16_t pitches[108] = {    0, 3609, 3406, 3214, 3034, 2863, 2704, 2551, 2408, 2273, 2145, 2025,     //   0
                                       1912, 1804, 1703, 1607, 1517, 1432, 1352, 1276, 1204, 1137, 1073, 1013,     //   1
                                        956,  902,  852,  804,  759,  716,  676,  638,  602,  568,  537,  506,     //   2
                                        478,  451,  426,  402,  379,  358,  338,  319,  301,  284,  268,  253,     //   3
                                        239,  226,  213,  201,  190,  179,  169,  160,  151,  142,  134,  127,     //   4
                                        120,  113,  107,  101,   95,   90,   85,   80,   75,   71,   67,   64,     //   5
                                         60,   57,   53,   50,   48,   45,   42,   40,   38,   36,   34,   32,     //   6
                                         30,   28,   27,   25,   24,   23,   21,   20,   19,   18,   17,   16,     //   7
                                         15,   14,   13,   13,   12,   11,   11,   10,    9,    9,    8,    8      //   8  Not precise enough
};


void setup()
{
  init_SID(); //Output on pin 3
  setADCrate(1);
  for (byte i = 8; i < 13; i++) 
  {
    pinMode(i, OUTPUT);
  }
}

void loop()
{
  melodyExample();
}


//// здесь выдаём ноту исходя из внешних параметров
uint8_t prepare_frame(const uint8_t channel_array[], const int channel_array_size, int& channel_step, uint8_t& steps_left)
{
  uint8_t result = 0;
    if (steps_left == 0)                                                // если нули отыграли, то нужно подтянуть новую ноту
    { 
      if (channel_step < channel_array_size)                            // пока массив не закончился
      {
        uint8_t note = pgm_read_byte(&channel_array[channel_step]);     // дёргаем из массива ноту
        if (note > 107)                                                 // если номер ноты больше 107, значит это "длинный" нуль
        {
          steps_left = note - 107 - 1;                                  // извлекаем из номера длительность нуля
          result = 0;                                                   // и возвращаем... что бы вы подумали?   правильно, нуль
          channel_step += 1;                                            // увеличиваем счётчик текущего массива, чтобы перещёлкнуться на следующую ноту
        }

        else
        {
          result = note;                                                // если номер ноты меньше 107, то это обычная нота и мы просто возвращаем её
          channel_step += 1;                                            // а счётчик текущего массива перещёлкиваем на следующий элемент
        }
      }

      else
      {
        result = 0;                                                     // если закончился массив (channel_step >= channel_array_size) и последняя нота отзвучала (steps_left == 0), то просто до победного молчим как партизаны
      }
    }
      
    else 
    { 
      steps_left -= 1;                                                  // если "длинному" нулю есть куда звучать, то уменьшаем счётчик оствашихся шагов (счётчик длительности)
      result = 0;                                                       // и возвращаем [хотел написать ничто, но у нас для этого есть null. а ноль - это уже что-то]
    }
  return result;  
}


void playNoise()
{

  uint8_t noise_frame[NUMBER_OF_CHANNELS] = {0, 0, 0, 0, Nb_DS2};
  
  for (int i = 0; i < NUMBER_OF_CHANNELS; ++i)
  {
    channels[i]->note = pitches[noise_frame[i]];
  }
  delay(25);
  noise.note = N_NOP;
}


void melodyExample()
{
  /*
   * squares[0] = channels[0]
   * squares[1] = channels[1]
   * triangle   = channels[2]
   * sawtooth   = channels[3]
   * noise      = channels[4]
   */
  
  int melody_i = 0;
  noise.volume = 10; // last 8, default 15
  squares[1].volume = 10;

  set_square_duty_cycle(squares[1], 2);
  
  uint8_t current_note_steps_left[NUMBER_OF_CHANNELS] = {};  // здесь будет храниться количество шагов, которое ещё дложен играться 0
  uint8_t current_frame[NUMBER_OF_CHANNELS] = {};            // здесь будут собираться ноты, которые будут скормлены шарманке не текущем шаге
  uint8_t default_volume[NUMBER_OF_CHANNELS] = {};           // здесь будут храниться значения громкости, установленные изначально
  float current_volume[NUMBER_OF_CHANNELS] = {};             // здесь будут храниться значения громкости, установленные изначально
  uint8_t volume_release_first_step = 4;                     // первый шаг уменьшения громкости во время релиза
  float volume_release_step = 1.5;                           // шаг уменьшения громкости во время релиза, единиц на шаг ( TODO потом подумать, может сделать наоборот, длину релиза в шагах, а из неё считать шаг)
  int current_step[NUMBER_OF_CHANNELS] = {};                 // из-за нелинейности перемещения по массивам нот приходится хранить текущий шаг для каждого массива

  // для старта заполним всё нулями
  for (int i = 0; i < NUMBER_OF_CHANNELS; ++i) 
  {
    current_step[i] = 0; 
    current_frame[i] = 0;
    default_volume[i] = channels[i]->volume;
    current_volume[i] = channels[i]->volume;
    current_note_steps_left[i] = 0;
  }

 
  while (true)
  {
    //   здесь будет расчёт релиза
    for (int i = 0; i < NUMBER_OF_CHANNELS; ++i) {
      // если на канале отключён релиз, то просто считываем ноту во фрейм
      if (not MELODY_RELEASE_CHANNELS[i]) {
        current_frame[i] = pgm_read_byte(&melody[i][melody_i]);
      }
      // если у нас на текущем шаге будет играть нота, то громкость выставляем на дефолтную, и считываем её во фрейм
      else if (pgm_read_byte(&melody[i][melody_i]) > 0) {
        channels[i]->volume = default_volume[i];
        current_volume[i] = default_volume[i];
        current_frame[i] = pgm_read_byte(&melody[i][melody_i]);
      }
      // если нота только закончилась, то чуть сильнее уменьшаем громкость
      else if (pgm_read_byte(&melody[i][melody_i - 1]) != 0 and pgm_read_byte(&melody[i][melody_i]) == 0) {
        current_volume[i] -= volume_release_first_step;
        channels[i]->volume = round(current_volume[i]);
        if (current_volume[i] <= 0) {
          channels[i]->volume = 0;
          current_frame[i] = 0;
          current_volume[i] = 0;
        }
      }
      // иначе просто уменьшаем громкость, пока есть куда
      else if (channels[i]->volume > 0){
        current_volume[i] -= volume_release_step;
        channels[i]->volume = round(current_volume[i]);
        if (current_volume[i] <= 0) {
          channels[i]->volume = 0;
          current_frame[i] = 0;
          current_volume[i] = 0;
        }
      }      
    }
    

    // здесь формируем следующий кадр нот
    // если номер ноты n больше 107, то это n - 107 идущих подряд нулей
    //                                массив нот        размер массива нот   текущий шаг канала     оставш. кол-во 0
    // current_frame[0] = prepare_frame(melody_channel_0, MELODY_CHANNEL_0_SIZE, current_step[0], current_note_steps_left[0]);
    // current_frame[1] = prepare_frame(melody_channel_1, MELODY_CHANNEL_1_SIZE, current_step[1], current_note_steps_left[1]);
    // current_frame[2] = prepare_frame(melody_channel_2, MELODY_CHANNEL_2_SIZE, current_step[2], current_note_steps_left[2]);
    // current_frame[3] = prepare_frame(melody_channel_3, MELODY_CHANNEL_3_SIZE, current_step[3], current_note_steps_left[3]);
    // current_frame[4] = prepare_frame(melody_channel_4, MELODY_CHANNEL_4_SIZE, current_step[4], current_note_steps_left[4]);

    for (int i = 0; i < NUMBER_OF_CHANNELS; ++i)
    {
      channels[i]->note = pitches[current_frame[i]];
      // channels[i]->note = pitches[pgm_read_byte(&melody[i][melody_i])]; //Read melody from PROGMEM (melodies.h)

      // Leds
      if (pitches[pgm_read_byte(&melody[i][melody_i])] > 0)
      {
        setPin(i+8, 1);
      }
      else
      {
        setPin(i+8, 0);
      }
    }
        
    //Cut square2 and noise short
    delay(FIRST_DELAY);   // default 35

    for (int i = 0; i < NUMBER_OF_CHANNELS; ++i)
    {
      if (pgm_read_byte(&melody[i][melody_i+1]) != pgm_read_byte(&melody[i][melody_i]))
      {
        setPin(i+8, 0);
      }
    }


  //    // channel 0
  //    if ((current_note_steps_left[0] == 0) and (pgm_read_byte(&melody_channel_0[current_step[0]]) != current_frame[0]))
  //    {
  //      setPin(8, 0);
  //    }
  //
  //    // channel 1
  //    if ((current_note_steps_left[1] == 0) and (pgm_read_byte(&melody_channel_1[current_step[1]]) != current_frame[1]))
  //    {
  //      setPin(9, 0);
  //    }
  //
  //    // channel 2
  //    if ((current_note_steps_left[2] == 0) and (pgm_read_byte(&melody_channel_2[current_step[2]]) != current_frame[2]))
  //    {
  //      setPin(10, 0);
  //    }
  //
  //    // channel 3
  //    if ((current_note_steps_left[3] == 0) and (pgm_read_byte(&melody_channel_3[current_step[3]]) != current_frame[3]))
  //    {
  //      setPin(11, 0);
  //    }
  //
  //    // channel 4
  //    if ((current_note_steps_left[4] == 0) and (pgm_read_byte(&melody_channel_4[current_step[4]]) != current_frame[4]))
  //    {
  //      setPin(12, 0);
  //    }


    delay(15);
    noise.note = N_NOP;
    delay(SECOND_DELAY);
      
    melody_i = (melody_i + 1) % MELODY_LENGTH;
    if (melody_i == 0)
    {
      for (int i = 0; i < NUMBER_OF_CHANNELS; ++i) 
      {
        current_step[i] = 0; 
        current_frame[i] = 0;
        current_note_steps_left[i] = 0;
      }    
    }
  }
}
